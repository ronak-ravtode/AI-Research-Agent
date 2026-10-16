import asyncio
import json
import random
import re
from typing import Optional

from groq import AsyncGroq

from app.core.config import get_settings
from app.core.logging import logger

# Transient provider conditions worth retrying. A rate limit is not a failure of the
# request: the free Groq tier is capped per minute, so backing off and trying again
# usually succeeds within seconds.
RETRYABLE_MARKERS = (
    "rate limit",
    "rate_limit",
    "429",
    "timeout",
    "timed out",
    "overloaded",
    "503",
    "502",
    "500",
    "connection",
    "temporarily unavailable",
)

MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 2.0
BACKOFF_CAP_SECONDS = 20.0


def is_transient(message: str) -> bool:
    lowered = (message or "").lower()
    return any(marker in lowered for marker in RETRYABLE_MARKERS)


class LLMService:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    async def _complete(self, messages, temperature, max_tokens) -> str:
        """One completion, with bounded backoff on transient provider errors."""
        last_error: Exception | None = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except Exception as exc:  # noqa: BLE001 - inspected below
                last_error = exc
                if attempt == MAX_ATTEMPTS or not is_transient(str(exc)):
                    raise
                delay = min(
                    BACKOFF_CAP_SECONDS,
                    BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)),
                )
                # Jitter keeps concurrent retries from re-colliding on the same second.
                delay += random.uniform(0, delay * 0.25)
                logger.warning(
                    "Transient model error, retrying",
                    data={
                        "attempt": attempt,
                        "max_attempts": MAX_ATTEMPTS,
                        "retry_in_seconds": round(delay, 1),
                        "error": type(exc).__name__,
                    },
                )
                await asyncio.sleep(delay)

        raise last_error  # pragma: no cover - unreachable

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self._complete(messages, temperature, max_tokens)

    async def structured_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict:
        response_text = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        cleaned = (response_text or "").strip()

        json_match = re.search(r"```json\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(1).strip()
        else:
            for prefix in ["```json", "```"]:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            first_brace = cleaned.find("{")
            last_brace = cleaned.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                return json.loads(cleaned[first_brace:last_brace + 1])
            raise


llm_service = LLMService()
