"""
Shared test fixtures.

Uses an in-memory SQLite database so tests never touch the real PostgreSQL
instance and can run in CI without any external services.

External services patched out:
  - Database  → SQLite (aiosqlite)
  - Redis     → fakeredis (rate limiter + any other Redis usage)
  - Celery    → stubs (tasks never dispatch)
"""
from __future__ import annotations

import pytest
import pytest_asyncio
import fakeredis.aioredis as fakeredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base
from api.deps import get_db
from api.main import app
import api.ratelimit as ratelimit_module

# ── In-memory SQLite engine ────────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
_TestSession = sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def _create_tables():
    """Create all tables before each test and drop them after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def _fake_redis_global():
    """Replace the shared Redis client with in-memory fakeredis for every test."""
    original = ratelimit_module._redis
    ratelimit_module._redis = fakeredis.FakeRedis()
    yield
    ratelimit_module._redis = original


@pytest_asyncio.fixture()
async def db_session():
    """Yield a fresh database session backed by SQLite."""
    async with _TestSession() as session:
        yield session


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession):
    """
    AsyncClient wired to the FastAPI app with the test DB injected.
    Celery task dispatch and Redis are both stubbed so no external
    services are needed.
    """
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    # Stub Celery so tasks never actually dispatch
    import api.workers.tasks as tasks_module  # noqa: PLC0415
    tasks_module.run_simulation.delay = lambda *a, **kw: None  # type: ignore[attr-defined]
    tasks_module.run_sweep.delay = lambda *a, **kw: None  # type: ignore[attr-defined]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
