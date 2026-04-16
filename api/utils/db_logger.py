"""
Optional database log handler.

When LOG_TO_DB=true, important application events are persisted to app_logs.
The handler does fire-and-forget inserts using a fresh session per write so
failures don't block the calling code.
"""

import asyncio
import json
import logging

from sqlalchemy import text

from api.config import settings
from api.database import AsyncSessionLocal


class DBLogHandler(logging.Handler):
    """Writes log records to the app_logs table."""

    def __init__(self, service: str) -> None:
        super().__init__(level=logging.WARNING)
        self.service = service

    def emit(self, record: logging.LogRecord) -> None:
        try:
            asyncio.create_task(self._write(record))
        except RuntimeError:
            # No running loop — caller is in sync context. Skip.
            pass

    async def _write(self, record: logging.LogRecord) -> None:
        details = None
        if record.exc_info:
            details = {"exc_type": str(record.exc_info[0]), "exc_msg": str(record.exc_info[1])}
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    text(
                        """
                        INSERT INTO app_logs
                            (level, service, operation, message, details)
                        VALUES
                            (:level, :service, :operation, :message, :details)
                        """
                    ),
                    {
                        "level": record.levelname,
                        "service": self.service,
                        "operation": record.name,
                        "message": record.getMessage(),
                        "details": json.dumps(details) if details else None,
                    },
                )
                await session.commit()
        except Exception:
            # Logging must never raise into the app.
            pass


def install_db_logger(service: str) -> None:
    """Attach the DB log handler to the root logger if LOG_TO_DB is enabled."""
    if not settings.log_to_db:
        return
    handler = DBLogHandler(service=service)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(handler)
