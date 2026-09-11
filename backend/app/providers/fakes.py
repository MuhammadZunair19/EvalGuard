import hashlib
import math
import re

from backend.app.providers.base import VectorRecord


class DeterministicEmbeddingProvider:
    dimensions = 64

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in re.findall(r"[a-z0-9]+", text.lower()):
                digest = hashlib.sha256(token.encode()).digest()
                vector[int.from_bytes(digest[:2], "big") % self.dimensions] += 1
            norm = math.sqrt(sum(value * value for value in vector)) or 1
            vectors.append([value / norm for value in vector])
        return vectors


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.items: dict[str, tuple[VectorRecord, list[float]]] = {}

    async def upsert(self, records: list[VectorRecord], embeddings: list[list[float]]) -> None:
        self.items.update(
            {
                record.id: (record, vector)
                for record, vector in zip(records, embeddings, strict=True)
            }
        )

    async def query(self, embedding: list[float], top_k: int) -> list[VectorRecord]:
        scored = []
        for record, vector in self.items.values():
            score = sum(left * right for left, right in zip(embedding, vector, strict=True))
            scored.append(VectorRecord(record.id, record.text, record.metadata, score))
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]

    async def delete_document(self, document_id: str) -> None:
        self.items = {
            key: value
            for key, value in self.items.items()
            if value[0].metadata["document_id"] != document_id
        }


class DeterministicLLMProvider:
    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self.responses = responses or {}

    async def generate(self, prompt: str, system_prompt: str) -> str:
        for marker, answer in self.responses.items():
            if marker.lower() in prompt.lower():
                return answer
        return "I don't have enough information in the provided documents."
