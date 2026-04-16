"""
Claude API client wrapper.

All Anthropic API calls go through this class. Direct use of the SDK is
prohibited so that retries, logging, and prompt-loading stay consistent.

The client is created lazily on first use so the app can boot without an
Anthropic key (useful for the scheduler container or local dev without AI).
"""

import logging
import time

import anthropic

from api.config import settings


logger = logging.getLogger(__name__)


class ClaudeNotConfiguredError(RuntimeError):
    """Raised when Claude is invoked without ANTHROPIC_API_KEY set."""


class ClaudeClient:
    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            if not settings.anthropic_api_key:
                raise ClaudeNotConfiguredError(
                    "ANTHROPIC_API_KEY is not set — cannot call Claude API"
                )
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str = "claude-sonnet-4-6",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Send a single completion to Claude and return the text response."""
        client = self._get_client()
        start = time.time()

        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
        except anthropic.APIError as exc:
            duration_ms = int((time.time() - start) * 1000)
            logger.error("Claude API error after %dms: %s", duration_ms, str(exc))
            raise

        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            "Claude API call completed in %dms (model=%s, in=%d, out=%d)",
            duration_ms,
            model,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        return response.content[0].text

    async def complete_with_prompt(
        self,
        db,
        prompt_key: str,
        user_message: str,
        variables: dict | None = None,
    ) -> str:
        """Combine prompt_service + complete: load prompt by key, render, send."""
        from api.utils.prompt_service import render_prompt

        prompt = await render_prompt(db, prompt_key, variables or {})
        return self.complete(
            system_prompt=prompt["content"],
            user_message=user_message,
            model=prompt["model"],
            temperature=prompt["temperature"],
            max_tokens=prompt["max_tokens"],
        )


claude = ClaudeClient()
