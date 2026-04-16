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
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

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
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine):
    """
    Per-test session inside a transaction that gets rolled back.

    Note: `get_db` in the app calls `commit()` on success — we override the
    dependency in the `client` fixture to use a no-commit version.
    """
    async with test_engine.connect() as connection:
        trans = await connection.begin()
        session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
        async with session_factory() as session:
            try:
                yield session
            finally:
                await trans.rollback()


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        # Yield without commit — the transaction will be rolled back by the `db` fixture.
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"x-api-key": settings.api_key},
    ) as client:
        yield client
    app.dependency_overrides.clear()
