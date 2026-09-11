from fastapi import APIRouter

from backend.app.api.documents import router as documents_router
from backend.app.api.rag import router as rag_router

router = APIRouter()
router.include_router(documents_router)
router.include_router(rag_router)


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "evalguard-api"}
