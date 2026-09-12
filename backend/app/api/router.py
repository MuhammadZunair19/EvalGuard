from fastapi import APIRouter, Depends

from backend.app.api.documents import router as documents_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.rag import router as rag_router
from backend.app.api.reporting import router as reporting_router
from backend.app.core.config import Settings, get_settings

router = APIRouter()
router.include_router(documents_router)
router.include_router(evaluation_router)
router.include_router(rag_router)
router.include_router(reporting_router)


@router.get("/health", tags=["system"])
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str | int]:
    return {
        "status": "healthy",
        "service": "evalguard-api",
        "ollama_model": settings.ollama_model,
        "provider_mode": settings.provider_mode,
        "default_top_k": settings.default_top_k,
    }
