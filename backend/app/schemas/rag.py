from pydantic import BaseModel, Field


class RAGQuery(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    prompt_version_id: str | None = None


class RetrievedSource(BaseModel):
    document_id: str
    document_name: str
    chunk_id: str
    content: str
    similarity_score: float


class RAGResponse(BaseModel):
    answer: str
    sources: list[RetrievedSource]
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
