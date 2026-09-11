import statistics
from collections import defaultdict
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.evaluation.classification import classify_failure
from backend.app.evaluation.retrieval import calculate_retrieval_metrics
from backend.app.evaluators import AnswerRelevanceEvaluator, CitationValidator, ContextPrecisionEvaluator, ContextRecallEvaluator, CorrectnessEvaluator, FaithfulnessEvaluator, HallucinationEvaluator
from backend.app.evaluators.base import EvaluationInput, EvaluationOutput, overlap
from backend.app.models.entities import EvaluationDataset, EvaluationRun, MetricResult, RunStatus, TestCase, TestResult
from backend.app.schemas.evaluation import EvaluationRunCreate
from backend.app.services.rag import RAGService

logger = structlog.get_logger()


class EvaluationService:
    evaluators = [AnswerRelevanceEvaluator(), FaithfulnessEvaluator(), ContextPrecisionEvaluator(), ContextRecallEvaluator(), CorrectnessEvaluator(), HallucinationEvaluator(), CitationValidator()]

    def __init__(self, session: AsyncSession, rag: RAGService, settings: Settings) -> None:
        self.session, self.rag, self.settings = session, rag, settings

    async def execute(self, request: EvaluationRunCreate) -> EvaluationRun:
        dataset = await self.session.get(EvaluationDataset, request.dataset_id)
        if dataset is None:
            raise AppError("DATASET_NOT_FOUND", "Evaluation dataset was not found.", 404)
        cases = list((await self.session.scalars(select(TestCase).where(TestCase.dataset_id == dataset.id).order_by(TestCase.created_at))).all())
        if not cases:
            raise AppError("EMPTY_DATASET", "The evaluation dataset contains no test cases.")
        thresholds = {**request.thresholds}
        run = EvaluationRun(dataset_id=dataset.id, prompt_version_id=request.prompt_version_id, model=request.model, embedding_model=self.settings.embedding_model, top_k=request.top_k, chunk_configuration={"size": 900, "overlap": 120}, thresholds=thresholds, status=RunStatus.RUNNING, test_count=len(cases))
        self.session.add(run)
        await self.session.flush()
        logger.info("evaluation_run_started", run_id=run.id, test_count=len(cases))
        all_metrics: dict[str, list[float]] = defaultdict(list)
        retrieval_values = defaultdict(list)
        latencies, passed_count = [], 0
        for case in cases:
            rag_outputs = [await self.rag.query(case.question, request.top_k) for _ in range(case.repetitions)]
            response = rag_outputs[0]
            contexts = [source.content for source in response.sources]
            item = EvaluationInput(case.question, response.answer, contexts, case.expected_answer, case.expected_facts)
            results = {evaluator.metric: evaluator.evaluate(item, thresholds.get(evaluator.metric, 0.8)) for evaluator in self.evaluators}
            retrieval = calculate_retrieval_metrics(response.sources, case.expected_document, case.expected_chunk)
            consistency = 1.0 if len(rag_outputs) == 1 else statistics.mean(overlap(rag_outputs[0].answer, candidate.answer) for candidate in rag_outputs[1:])
            results["consistency"] = EvaluationOutput("consistency", round(consistency, 4), consistency >= thresholds.get("consistency", 0.8), thresholds.get("consistency", 0.8), "Semantic agreement across repeated responses.")
            failure = classify_failure(results, retrieval.hit_rate, response.total_latency_ms, thresholds.get("p95_latency_ms", 3000), case.test_type)
            passed = failure is None
            passed_count += int(passed)
            test_result = TestResult(run_id=run.id, test_case_id=case.id, passed=passed, actual_answer=response.answer, retrieved_context=[source.model_dump() for source in response.sources], failure_type=failure, latency_ms=response.total_latency_ms, unsupported_claims=results["hallucination"].unsupported_claims)
            self.session.add(test_result)
            await self.session.flush()
            for result in results.values():
                self.session.add(MetricResult(test_result_id=test_result.id, metric=result.metric, score=result.score, passed=result.passed, threshold=result.threshold, details=result.details))
                all_metrics[result.metric].append(result.score)
            for key, value in retrieval.__dict__.items():
                retrieval_values[key].append(value)
            latencies.append(response.total_latency_ms)
        summary = self._summary(all_metrics, retrieval_values, latencies)
        failed_gates = self._failed_gates(summary, thresholds)
        run.pass_count = passed_count
        run.fail_count = len(cases) - passed_count
        run.pass_percentage = round(passed_count / len(cases) * 100, 2)
        run.summary = {**summary, "failed_gates": failed_gates}
        run.status = RunStatus.PASSED if not failed_gates and run.fail_count == 0 else RunStatus.FAILED
        run.completed_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(run)
        logger.info("test_run_completed", run_id=run.id, status=run.status)
        return run

    @staticmethod
    def _summary(metrics, retrieval, latencies):
        percentile_index = max(0, round(0.95 * len(latencies) + 0.5) - 1)
        sorted_latencies = sorted(latencies)
        data = {name: round(statistics.mean(values), 4) for name, values in metrics.items()}
        data.update({name: round(statistics.mean(values), 4) for name, values in retrieval.items()})
        data["hallucination_rate"] = data.pop("hallucination", 0.0)
        data["latency"] = {"average": round(statistics.mean(latencies), 2), "min": min(latencies), "max": max(latencies), "p50": round(statistics.median(latencies), 2), "p95": sorted_latencies[percentile_index]}
        return data

    @staticmethod
    def _failed_gates(summary, thresholds):
        mapping = {"retrieval_hit_rate": "hit_rate", "p95_latency_ms": "latency"}
        failed = []
        for gate, limit in thresholds.items():
            key = mapping.get(gate, gate)
            value = summary["latency"]["p95"] if gate == "p95_latency_ms" else summary.get("hallucination_rate" if gate == "hallucination" else key)
            if value is None:
                continue
            if (gate == "hallucination" or gate == "p95_latency_ms") and value > limit:
                failed.append({"gate": gate, "actual": value, "threshold": limit, "comparator": "<="})
            elif gate not in {"hallucination", "p95_latency_ms"} and value < limit:
                failed.append({"gate": gate, "actual": value, "threshold": limit, "comparator": ">="})
        return failed


def compare_runs(current: EvaluationRun, baseline: EvaluationRun) -> dict:
    if current.dataset_id != baseline.dataset_id:
        raise AppError("INCOMPARABLE_RUNS", "Runs must use the same evaluation dataset.")
    metric_names = ["faithfulness", "answer_relevance", "context_precision", "context_recall", "answer_correctness", "hallucination_rate", "hit_rate"]
    metrics = []
    for name in metric_names:
        left, right = baseline.summary.get(name, 0), current.summary.get(name, 0)
        delta = round(right - left, 4)
        regressed = delta > 0 if name == "hallucination_rate" else delta < 0
        metrics.append({"metric": name, "baseline": left, "current": right, "delta": delta, "regressed": regressed})
    base_latency, current_latency = baseline.summary.get("latency", {}).get("p95", 0), current.summary.get("latency", {}).get("p95", 0)
    metrics.append({"metric": "p95_latency_ms", "baseline": base_latency, "current": current_latency, "delta": round(current_latency - base_latency, 2), "regressed": current_latency > base_latency})
    return {"baseline_id": baseline.id, "current_id": current.id, "regression_detected": any(item["regressed"] for item in metrics), "metrics": metrics}

