from backend.app.evaluators.base import EvaluationOutput


def classify_failure(
    metrics: dict[str, EvaluationOutput],
    retrieval_hit: float,
    latency_ms: float,
    latency_limit: float,
    test_type: str,
) -> str | None:
    if retrieval_hit == 0:
        return "Retrieval Failure"
    if latency_ms > latency_limit:
        return "Latency Failure"
    if not metrics["hallucination"].passed:
        return "Prompt Injection Failure" if test_type == "prompt-injection" else "Hallucination"
    if not metrics["answer_correctness"].passed:
        return "Generation Failure"
    if not metrics["faithfulness"].passed:
        return "Missing Context"
    if not metrics["answer_relevance"].passed:
        return "Low Relevance"
    if not metrics["citation_validation"].passed:
        return "Citation Failure"
    return None
