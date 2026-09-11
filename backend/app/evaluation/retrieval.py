from dataclasses import dataclass

from backend.app.schemas.rag import RetrievedSource


@dataclass(frozen=True)
class RetrievalMetrics:
    hit_rate: float
    precision_at_k: float
    recall_at_k: float
    mrr: float


def calculate_retrieval_metrics(
    sources: list[RetrievedSource], expected_document: str | None, expected_chunk: str | None
) -> RetrievalMetrics:
    if not expected_document and not expected_chunk:
        return RetrievalMetrics(1.0, 1.0, 1.0, 1.0)
    matches = [
        source.chunk_id == expected_chunk
        if expected_chunk
        else source.document_name == expected_document
        for source in sources
    ]
    relevant = sum(matches)
    first_rank = next((index for index, match in enumerate(matches, 1) if match), None)
    hit = float(relevant > 0)
    return RetrievalMetrics(
        hit_rate=hit,
        precision_at_k=relevant / len(sources) if sources else 0.0,
        recall_at_k=hit,
        mrr=1 / first_rank if first_rank else 0.0,
    )
