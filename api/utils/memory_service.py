"""
Claude memory management.

Stores and retrieves per-context markdown files. Designed to be injected into
Claude prompts as long-term memory ("here's everything I know about user X").

Data lives in the `memory_files` table, keyed on (context_key, file_key).
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


async def read_memory(db: AsyncSession, context_key: str, file_key: str) -> str:
    """Return the markdown content of a single memory file (empty string if missing)."""
    result = await db.execute(
        text(
            """
            SELECT content FROM memory_files
            WHERE context_key = :context_key AND file_key = :file_key
            """
        ),
        {"context_key": context_key, "file_key": file_key},
    )
    row = result.fetchone()
    return row.content if row else ""


async def write_memory(
    db: AsyncSession, context_key: str, file_key: str, content: str
) -> None:
    """Upsert a memory file."""
    await db.execute(
        text(
            """
            INSERT INTO memory_files (context_key, file_key, content, updated_at)
            VALUES (:context_key, :file_key, :content, NOW())
            ON CONFLICT (context_key, file_key)
            DO UPDATE SET content = EXCLUDED.content, updated_at = NOW()
            """
        ),
        {"context_key": context_key, "file_key": file_key, "content": content},
    )
    logger.debug("Memory written: %s/%s", context_key, file_key)


async def get_full_context(db: AsyncSession, context_key: str) -> str:
    """Concatenate all memory files for a context as a single markdown string."""
    result = await db.execute(
        text(
            """
            SELECT file_key, content FROM memory_files
            WHERE context_key = :context_key
            ORDER BY updated_at DESC
            """
        ),
        {"context_key": context_key},
    )
    rows = result.fetchall()
    if not rows:
        return ""
    return "\n\n".join(f"## {row.file_key}\n{row.content}" for row in rows)
