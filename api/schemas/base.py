"""Shared Pydantic helpers."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for response schemas that load from SQLAlchemy ORM rows."""

    model_config = ConfigDict(from_attributes=True)


class TimestampedResponse(ORMModel):
    """Mixin for resources that expose id + timestamps."""

    id: UUID
    created_at: datetime
    updated_at: datetime
