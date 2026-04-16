"""
Hello-world endpoints — smoke tests for both layers of the stack.

    GET /api/v1/hello      → confirms FastAPI is responding
    GET /api/v1/hello/db   → confirms FastAPI can read from Postgres

Both are protected by the API key (see registration in api/main.py), so a
successful 200 also proves the auth chain works.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.hello import HelloMessage
from api.schemas.hello import HelloResponse


router = APIRouter(prefix="/hello", tags=["hello"])


@router.get("", response_model=HelloResponse)
async def hello() -> HelloResponse:
    return HelloResponse(message="hello world from FastAPI", source="fastapi")


@router.get("/db", response_model=HelloResponse)
async def hello_db(db: AsyncSession = Depends(get_db)) -> HelloResponse:
    result = await db.execute(
        select(HelloMessage).order_by(HelloMessage.created_at.asc()).limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return HelloResponse(message="(no rows in hello_messages)", source="database")
    return HelloResponse(message=row.message, source="database")
