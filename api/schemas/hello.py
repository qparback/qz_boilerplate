"""Pydantic response schema for the /v1/hello smoke-test endpoints."""

from pydantic import BaseModel


class HelloResponse(BaseModel):
    message: str
    source: str  # "fastapi" or "database"
