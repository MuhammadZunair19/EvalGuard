from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "EvalGuard"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://evalguard:evalguard@localhost:5432/evalguard"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_num_predict: int = Field(default=128, ge=16, le=4096)
    ollama_keep_alive: str = "30m"
    embedding_model: str = "all-MiniLM-L6-v2"
    provider_mode: str = "local"
    chroma_path: Path = Path("backend/data/chroma")
    upload_path: Path = Path("backend/data/uploads")
    default_top_k: int = Field(default=5, ge=1, le=20)
    max_upload_size: int = Field(default=10 * 1024 * 1024, ge=1024)


@lru_cache
def get_settings() -> Settings:
    return Settings()
