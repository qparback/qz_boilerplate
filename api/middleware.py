"""
Request middleware.

Attaches a short request ID to every request (`request.state.request_id`) so
logs across services can be correlated. Also logs every non-health request
with method, path, status, and duration.
"""

import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = uuid.uuid4().hex[:8]
        request.state.request_id = request_id
        start = time.time()

        response = await call_next(request)

        duration_ms = int((time.time() - start) * 1000)
        response.headers["X-Request-ID"] = request_id

        if request.url.path != "/health":
            logger.info(
                "%s %s %d %dms [%s]",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                request_id,
            )
        return response
