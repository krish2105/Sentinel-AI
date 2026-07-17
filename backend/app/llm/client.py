"""Provider-agnostic async LLM client.

Order of preference:
  1. Groq free tier (OpenAI-compatible) when ``GROQ_API_KEY`` is set.
  2. Ollama local when ``OLLAMA_BASE_URL`` is set.
  3. Deterministic **mock engine** otherwise — so every feature works with no
     keys, no network, no bill. The mock engine is *not* random: it produces
     realistic, structured attacker payloads and judge verdicts so demos and
     tests are reproducible.

All callers use :func:`complete` (freeform) or :func:`complete_json`
(structured). Never trust model output as code — outputs are only ever parsed
as data.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.llm.mock_engine import mock_chat
from app.observability.tracing import log_generation

Message = Dict[str, str]


class LLMClient:
    def __init__(self) -> None:
        self._provider = self._detect_provider()

    def _detect_provider(self) -> str:
        if settings.force_mock_llm:
            return "mock"
        if settings.groq_api_key:
            return "groq"
        if settings.ollama_base_url:
            return "ollama"
        return "mock"

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model_name(self) -> str:
        if self._provider == "groq":
            return settings.groq_model
        if self._provider == "ollama":
            return settings.ollama_model
        return "mock-engine"

    async def complete(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        purpose: str = "generic",
        trace: Any = None,
    ) -> str:
        """Return a single completion string for a chat message list.

        ``trace`` is an optional Langfuse trace handle (see
        ``app.observability.tracing``); when tracing is disabled it is ``None``
        and every call below is a no-op, so this costs nothing by default.
        """
        if self._provider == "groq":
            try:
                result = await self._groq(messages, temperature, max_tokens)
            except Exception:  # pragma: no cover - network fallback
                result = mock_chat(messages, purpose=purpose)
        elif self._provider == "ollama":
            try:
                result = await self._ollama(messages, temperature, max_tokens)
            except Exception:  # pragma: no cover
                result = mock_chat(messages, purpose=purpose)
        else:
            result = mock_chat(messages, purpose=purpose)

        log_generation(
            trace, name=purpose, model=self.model_name, prompt=messages,
            completion=result, metadata={"temperature": temperature},
        )
        return result

    async def complete_json(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        purpose: str = "generic",
        trace: Any = None,
    ) -> Dict[str, Any]:
        """Return parsed JSON. Falls back to mock JSON on parse failure."""
        raw = await self.complete(
            messages, temperature=temperature, max_tokens=max_tokens,
            purpose=purpose, trace=trace,
        )
        parsed = _extract_json(raw)
        if parsed is None:
            # Retry once against the deterministic engine for a valid shape.
            parsed = _extract_json(mock_chat(messages, purpose=purpose))
        return parsed or {}

    async def _groq(
        self, messages: List[Message], temperature: float, max_tokens: int
    ) -> str:
        async with httpx.AsyncClient(timeout=settings.llm_request_timeout) as client:
            resp = await client.post(
                f"{settings.groq_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _ollama(
        self, messages: List[Message], temperature: float, max_tokens: int
    ) -> str:
        async with httpx.AsyncClient(timeout=settings.llm_request_timeout) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    # Direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # Fenced ```json ... ```
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except Exception:
            pass
    # First balanced object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None


_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
