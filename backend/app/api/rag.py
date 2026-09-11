from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_providers
from backend.app.core.errors import AppError
from backend.app.db.session import get_session
from backend.app.models.entities import PromptVersion
from backend.app.schemas.rag import RAGQuery, RAGResponse
from backend.app.services.rag import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


def service(providers=Depends(get_providers)) -> RAGService:
    llm, embeddings, vectors = providers
    return RAGService(llm, embeddings, vectors)


@router.post("/query", response_model=RAGResponse)
async def query_rag(
    payload: RAGQuery,
    rag: RAGService = Depends(service),
    session: AsyncSession = Depends(get_session),
) -> RAGResponse:
    if payload.prompt_version_id:
        prompt = await session.get(PromptVersion, payload.prompt_version_id)
        if prompt is None:
            raise AppError("PROMPT_NOT_FOUND", "Prompt version was not found.", 404)
        return await rag.query(
            payload.question,
            payload.top_k,
            system_prompt=prompt.system_prompt,
            prompt_template=prompt.template,
        )
    return await rag.query(payload.question, payload.top_k)
