import pytest

from backend.app.evaluation.retrieval import calculate_retrieval_metrics
from backend.app.schemas.rag import RetrievedSource


def source(name: str, chunk: str, score: float = 0.9) -> RetrievedSource:
    return RetrievedSource(document_id=name, document_name=name, chunk_id=chunk, content="text", similarity_score=score)


@pytest.mark.regression
def test_retrieval_metrics_report_rank_and_precision():
    metrics = calculate_retrieval_metrics(
        [source("news.md", "1"), source("employee_handbook.md", "2"), source("guide.md", "3")],
        "employee_handbook.md",
        None,
    )
    assert metrics.hit_rate == 1
    assert metrics.precision_at_k == pytest.approx(1 / 3)
    assert metrics.recall_at_k == 1
    assert metrics.mrr == 0.5


@pytest.mark.regression
def test_wrong_document_is_retrieval_failure():
    metrics = calculate_retrieval_metrics([source("company_news.md", "1")], "employee_handbook.md", None)
    assert metrics.hit_rate == 0
    assert metrics.mrr == 0

