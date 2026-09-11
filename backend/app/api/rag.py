from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_providers
from backend.app.schemas.rag import RAGQuery, RAGResponse
from backend.app.services.rag import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


def service(providers=Depends(get_providers)) -> RAGService:
    llm, embeddings, vectors = providers
    return RAGService(llm, embeddings, vectors)


@router.post("/query", response_model=RAGResponse)
async def query_rag(payload: RAGQuery, rag: RAGService = Depends(service)) -> RAGResponse:
    return await rag.query(payload.question, payload.top_k)
