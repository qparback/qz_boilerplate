"""
Generic async CRUD base.

Usage:
    class UserService(CRUDBase[User]):
        def __init__(self) -> None:
            super().__init__(User)

    user_service = UserService()
"""

from typing import Generic, TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import BaseModel
from api.schemas.pagination import PageParams, PaginatedResponse


ModelType = TypeVar("ModelType", bound=BaseModel)


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> ModelType | None:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_or_404(self, db: AsyncSession, id: UUID) -> ModelType:
        record = await self.get(db, id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} {id} not found",
            )
        return record

    async def list(
        self, db: AsyncSession, params: PageParams
    ) -> PaginatedResponse[ModelType]:
        count_result = await db.execute(select(func.count()).select_from(self.model))
        total = count_result.scalar() or 0

        result = await db.execute(
            select(self.model)
            .order_by(self.model.created_at.desc())
            .offset(params.offset)
            .limit(params.page_size)
        )
        items = list(result.scalars().all())
        return PaginatedResponse.create(items=items, total=total, params=params)

    async def create(self, db: AsyncSession, data: dict) -> ModelType:
        record = self.model(**data)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update(self, db: AsyncSession, id: UUID, data: dict) -> ModelType:
        record = await self.get_or_404(db, id)
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        await db.flush()
        await db.refresh(record)
        return record

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        record = await self.get(db, id)
        if not record:
            return False
        await db.delete(record)
        await db.flush()
        return True
