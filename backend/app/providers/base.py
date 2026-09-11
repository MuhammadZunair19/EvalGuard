from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VectorRecord:
    id: str
    text: str
    metadata: dict[str, str | int]
    score: float = 0.0


class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class LLMProvider(Protocol):
    async def generate(self, prompt: str, system_prompt: str) -> str: ...


class VectorStore(Protocol):
    async def upsert(self, records: list[VectorRecord], embeddings: list[list[float]]) -> None: ...

    async def query(self, embedding: list[float], top_k: int) -> list[VectorRecord]: ...

    async def delete_document(self, document_id: str) -> None: ...
