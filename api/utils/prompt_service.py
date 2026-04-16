"""
Prompt service — loads AI prompts from the database.

Prompts are NEVER hardcoded in Python. Always:
    1. Add a row to `prompts` (initial seed in 01_schema.sql, edits via admin UI)
    2. Reference it by `key` here

This way prompts can be tuned without redeploying.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


class PromptNotFoundError(Exception):
    """Raised when no active prompt exists for the requested key."""


async def get_prompt(db: AsyncSession, key: str) -> dict:
    """Load a prompt by key. Returns dict(content, model, temperature, max_tokens)."""
    result = await db.execute(
        text(
            """
            SELECT content, model, temperature, max_tokens
            FROM prompts
            WHERE key = :key AND active = TRUE
            """
        ),
        {"key": key},
    )
    row = result.fetchone()
    if not row:
        raise PromptNotFoundError(f"Prompt '{key}' not found in database")
    return {
        "content": row.content,
        "model": row.model,
        "temperature": row.temperature,
        "max_tokens": row.max_tokens,
    }


async def render_prompt(db: AsyncSession, key: str, variables: dict) -> dict:
    """Load a prompt and substitute {placeholders} with the provided variables."""
    prompt = await get_prompt(db, key)
    try:
        prompt["content"] = prompt["content"].format(**variables)
    except KeyError as exc:
        logger.error("Missing variable %s in prompt '%s'", exc, key)
        raise
    return prompt
