from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.api.dependencies import get_providers
from backend.app.core.config import Settings, get_settings
from backend.app.db.base import Base
from backend.app.db.session import get_session
from backend.app.main import app
from backend.app.providers.fakes import DeterministicEmbeddingProvider, DeterministicLLMProvider, InMemoryVectorStore


@pytest_asyncio.fixture
async def client(tmp_path) -> AsyncIterator[AsyncClient]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    embeddings = DeterministicEmbeddingProvider()
    vectors = InMemoryVectorStore()
    llm = DeterministicLLMProvider(
        {
            "annual leave": "Employees receive 25 annual leave days per year [1].",
            "daughter": "I don't have enough information in the provided documents.",
        }
    )
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        upload_path=tmp_path / "uploads",
        chroma_path=tmp_path / "chroma",
    )

    async def session_override() -> AsyncIterator[AsyncSession]:
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_providers] = lambda: (llm, embeddings, vectors)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()
    await engine.dispose()

