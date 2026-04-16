"""
Audit logging — append-only record of every data mutation.

Failures here are swallowed and logged; we never fail a user request because
the audit write failed. (If audit becomes critical for compliance, change the
catch to re-raise.)
"""

import json
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


async def log_mutation(
    db: AsyncSession,
    operation: str,
    resource: str,
    resource_id: str | None = None,
    actor_key: str | None = None,
    ip_address: str | None = None,
    request_id: str | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    """Insert a row into audit_log. operation must be CREATE / UPDATE / DELETE."""
    try:
        await db.execute(
            text(
                """
                INSERT INTO audit_log
                    (operation, resource, resource_id, actor_key, ip_address,
                     request_id, old_values, new_values)
                VALUES
                    (:operation, :resource, :resource_id, :actor_key, :ip_address,
                     :request_id, :old_values, :new_values)
                """
            ),
            {
                "operation": operation,
                "resource": resource,
                "resource_id": str(resource_id) if resource_id else None,
                "actor_key": actor_key,
                "ip_address": ip_address,
                "request_id": request_id,
                "old_values": json.dumps(old_values) if old_values else None,
                "new_values": json.dumps(new_values) if new_values else None,
            },
        )
    except Exception as exc:
        logger.error("Failed to write audit log: %s", str(exc))
