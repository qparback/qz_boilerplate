"""
HelloMessage model — backs the /v1/hello/db smoke-test endpoint.
Keep this around as a reference for the model pattern; safe to delete once
your real resources exist.
"""

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from api.models.base import BaseModel


class HelloMessage(BaseModel):
    __tablename__ = "hello_messages"

    message: Mapped[str] = mapped_column(Text, nullable=False)
