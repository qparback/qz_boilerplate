"""
API key authentication.

All protected routes depend on `verify_api_key`. The dependency returns a
short hash of the key — useful as `actor_key` in audit log entries.
"""

import hashlib
import secrets

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from api.config import settings


api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def hash_key(key: str) -> str:
    """Deterministic short hash — safe to store in audit logs."""
    return hashlib.sha256(key.encode()).hexdigest()[:16]


async def verify_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> str:
    if not api_key or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    request.state.actor_key = hash_key(api_key)
    return request.state.actor_key
