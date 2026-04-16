"""
Async SQLAlchemy 2.0 engine + session management.

Pattern:
    async def my_route(db: AsyncSession = Depends(get_db)):
        ...

The session is committed on clean exit and rolled back on exception.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from api.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.is_dev,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Shared declarative base for every ORM model."""


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency — yields a session, commits on success, rolls back on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
