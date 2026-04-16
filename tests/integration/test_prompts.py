"""Integration test for prompt loading from the database."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.utils.prompt_service import PromptNotFoundError, get_prompt, render_prompt


async def test_get_seeded_prompt(db: AsyncSession):
    prompt = await get_prompt(db, "example_system")
    assert prompt["content"]
    assert prompt["model"]
    assert isinstance(prompt["temperature"], float)
    assert isinstance(prompt["max_tokens"], int)


async def test_missing_prompt_raises(db: AsyncSession):
    with pytest.raises(PromptNotFoundError):
        await get_prompt(db, "this_key_does_not_exist")


async def test_render_prompt_substitutes_variables(db: AsyncSession):
    rendered = await render_prompt(
        db,
        "example_user_template",
        {"task": "summarize this", "context": "a paragraph"},
    )
    assert "summarize this" in rendered["content"]
    assert "a paragraph" in rendered["content"]
