from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import AppError
from backend.app.db.session import get_session
from backend.app.models.entities import EvaluationRun, MetricResult, TestCase, TestResult

router = APIRouter(tags=["reporting"])


@router.get("/dashboard")
async def dashboard(session: AsyncSession = Depends(get_session)) -> dict:
    runs = list((await session.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at))).all())
    latest = runs[-1] if runs else None
    trends = [
        {
            "id": run.id,
            "timestamp": run.created_at.isoformat(),
            "pass_rate": run.pass_percentage,
            "faithfulness": run.summary.get("faithfulness", 0),
            "answer_relevance": run.summary.get("answer_relevance", 0),
            "hallucination_rate": run.summary.get("hallucination_rate", 0),
            "p95_latency_ms": run.summary.get("latency", {}).get("p95", 0),
        }
        for run in runs[-12:]
    ]
    return {
        "total_runs": len(runs),
        "latest_pass_rate": latest.pass_percentage if latest else 0,
        "ai_quality_score": round(
            sum(latest.summary.get(name, 0) for name in ["faithfulness", "answer_relevance", "answer_correctness"]) / 3,
            4,
        ) if latest else 0,
        "hallucination_rate": latest.summary.get("hallucination_rate", 0) if latest else 0,
        "retrieval_hit_rate": latest.summary.get("hit_rate", 0) if latest else 0,
        "p95_latency_ms": latest.summary.get("latency", {}).get("p95", 0) if latest else 0,
        "trends": trends,
    }


@router.get("/evaluation-runs/{run_id}/results")
async def run_results(run_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    run = await session.get(EvaluationRun, run_id)
    if run is None:
        raise AppError("RUN_NOT_FOUND", "Evaluation run was not found.", 404)
    rows = (
        await session.execute(
            select(TestResult, TestCase)
            .join(TestCase, TestCase.id == TestResult.test_case_id)
            .where(TestResult.run_id == run_id)
            .order_by(TestResult.created_at)
        )
    ).all()
    results = []
    for result, case in rows:
        metrics = list((await session.scalars(select(MetricResult).where(MetricResult.test_result_id == result.id))).all())
        results.append(
            {
                "id": result.id,
                "test_case_id": case.id,
                "question": case.question,
                "test_type": case.test_type,
                "expected_answer": case.expected_answer,
                "expected_source": case.expected_document,
                "actual_answer": result.actual_answer,
                "retrieved_context": result.retrieved_context,
                "passed": result.passed,
                "failure_type": result.failure_type,
                "latency_ms": result.latency_ms,
                "unsupported_claims": result.unsupported_claims,
                "metrics": [
                    {"metric": metric.metric, "score": metric.score, "passed": metric.passed, "threshold": metric.threshold, "details": metric.details}
                    for metric in metrics
                ],
            }
        )
    failures = Counter(item["failure_type"] for item in results if item["failure_type"])
    return {"run": {"id": run.id, "status": run.status, "model": run.model, "summary": run.summary, "pass_percentage": run.pass_percentage}, "failure_breakdown": failures, "results": results}
