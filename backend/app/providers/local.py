import asyncio

import httpx

from backend.app.core.config import Settings
from backend.app.providers.base import VectorRecord


class SentenceTransformerEmbeddingProvider:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = await asyncio.to_thread(self.model.encode, texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


class OllamaLLMProvider:
    def __init__(
        self, base_url: str, model: str, num_predict: int = 128, keep_alive: str = "30m"
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.num_predict = num_predict
        self.keep_alive = keep_alive
        self.client = httpx.AsyncClient(timeout=180)

    async def generate(self, prompt: str, system_prompt: str) -> str:
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "keep_alive": self.keep_alive,
                "options": {"temperature": 0, "num_predict": self.num_predict},
            },
        )
        response.raise_for_status()
        return str(response.json()["response"]).strip()


class ChromaVectorStore:
    def __init__(self, path: str) -> None:
        import chromadb

        client = chromadb.PersistentClient(path=path)
        self.collection = client.get_or_create_collection("evalguard_documents")

    async def upsert(self, records: list[VectorRecord], embeddings: list[list[float]]) -> None:
        await asyncio.to_thread(
            self.collection.upsert,
            ids=[record.id for record in records],
            documents=[record.text for record in records],
            metadatas=[record.metadata for record in records],
            embeddings=embeddings,
        )

    async def query(self, embedding: list[float], top_k: int) -> list[VectorRecord]:
        result = await asyncio.to_thread(
            self.collection.query, query_embeddings=[embedding], n_results=top_k
        )
        records: list[VectorRecord] = []
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for vector_id, text, metadata, distance in zip(
            ids, documents, metadatas, distances, strict=True
        ):
            records.append(
                VectorRecord(
                    id=vector_id,
                    text=text,
                    metadata=metadata,
                    score=max(0.0, 1.0 - float(distance)),
                )
            )
        return records

    async def delete_document(self, document_id: str) -> None:
        await asyncio.to_thread(self.collection.delete, where={"document_id": document_id})


def build_local_providers(settings: Settings):
    return (
        OllamaLLMProvider(
            settings.ollama_base_url,
            settings.ollama_model,
            settings.ollama_num_predict,
            settings.ollama_keep_alive,
        ),
        SentenceTransformerEmbeddingProvider(settings.embedding_model),
        ChromaVectorStore(str(settings.chroma_path)),
    )
