from functools import lru_cache

from backend.app.core.config import get_settings
from backend.app.providers.local import build_local_providers


@lru_cache
def get_providers():
    return build_local_providers(get_settings())

