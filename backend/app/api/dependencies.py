from functools import lru_cache

from backend.app.core.config import get_settings
from backend.app.providers.fakes import (
    DeterministicEmbeddingProvider,
    DeterministicLLMProvider,
    InMemoryVectorStore,
)
from backend.app.providers.local import build_local_providers


@lru_cache
def get_providers():
    settings = get_settings()
    if settings.provider_mode == "deterministic":
        return DeterministicLLMProvider(), DeterministicEmbeddingProvider(), InMemoryVectorStore()
    return build_local_providers(settings)
