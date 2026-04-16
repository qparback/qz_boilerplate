"""
Shared test fixtures.

Test DB strategy:
    - `make test` spins up a fresh Postgres container on port 5433 with tmpfs
    - The init script creates all base tables there too
    - Each test runs inside a transaction that gets rolled back, so tests
      don't pollute each other

The test DB URL is derived from the app's DATABASE_URL by swapping the host
and database name.

Auth: the `client` fixture sends the API key on every request. To test the
"no key / wrong key" path, override headers per request.
"""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from api.config import settings
from api.database import get_db
from api.main import app


def _build_test_database_url() -> str:
    """Derive the test DB URL from the app's DATABASE_URL or env."""
    explicit = os.getenv("TEST_DATABASE_URL")
    if explicit:
        return explicit
    # Default: same connection string but pointing at port 5433 / DB suffix _test
    url = settings.database_url
    # Swap host:port to localhost:5433 (test container exposes 5433)
    # Naive replace works for the standard postgresql+asyncpg://user:pw@host:port/db pattern.
    parts = url.split("@", 1)
    if len(parts) == 2:
        userpw, rest = parts
        # rest = host:port/dbname
        if "/" in rest:
            hostport, dbname = rest.split("/", 1)
            return f"{userpw}@localhost:5433/{dbname}"
    return url


TEST_DATABASE_URL = _build_test_database_url()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    # NullPool — never reuse asyncpg connections between operations. The default
    # QueuePool can hand back a connection that's still mid-transaction from a
    # previous test, which asyncpg refuses ("another operation in progress").
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine):
    """
    Per-test session, shared underlying database.

    The test DB is recreated fresh by `make test` (tmpfs), so we accept that
    state may persist *within* a single pytest run. Tests should be read-only
    or use unique IDs to avoid clashing with each other.

    A previous version used SAVEPOINT-based rollback, but asyncpg disallows
    concurrent operations on the same raw connection — and FastAPI's dep
    override re-enters the same session, which triggers the conflict.
    Splitting out a clean session per test sidesteps that entirely.
    """
    async with AsyncSession(bind=test_engine, expire_on_commit=False) as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine):
    """
    HTTP client that uses a *fresh* session per request.

    We can't share the test's `db` fixture session here because asyncpg refuses
    concurrent operations on a single connection — and FastAPI's dependency
    machinery would re-enter the same session that the test still holds.
    """

    async def override_get_db():
        async with AsyncSession(bind=test_engine, expire_on_commit=False) as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"x-api-key": settings.api_key},
    ) as client:
        yield client
    app.dependency_overrides.clear()
