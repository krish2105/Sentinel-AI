"""Langfuse tracing — optional, graceful-degradation by design.

When ``LANGFUSE_PUBLIC_KEY`` / ``LANGFUSE_SECRET_KEY`` are unset (the zero-setup
default), every function here is a no-op, so the agent graph and LLM client run
with zero overhead and zero external calls. When keys are present, every run
becomes an inspectable trace: one span per node transition, one generation per
LLM call (model, prompt, completion, latency), so a reviewer can open Langfuse
and see exactly what the attacker/judge/target did on a given run.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

from app.config import settings

_enabled = bool(settings.langfuse_public_key and settings.langfuse_secret_key)


@lru_cache
def _client():
    if not _enabled:
        return None
    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception:
        return None


def enabled() -> bool:
    return _client() is not None


def trace_url(trace_id: str) -> Optional[str]:
    """Build a deep-link to a run's trace in the Langfuse UI.

    Returns None when tracing is disabled so callers can hide the link. The
    ``/trace/{id}`` path resolves to the trace within the keys' project.
    """
    if not enabled() or not trace_id:
        return None
    host = settings.langfuse_host.rstrip("/")
    return f"{host}/trace/{trace_id}"


def start_trace(trace_id: str, name: str, metadata: Optional[dict] = None):
    """Start (or resume) a trace for a run. Returns None when tracing is off."""
    client = _client()
    if not client:
        return None
    try:
        return client.trace(id=trace_id, name=name, metadata=metadata or {})
    except Exception:
        return None


def log_generation(
    trace: Any,
    name: str,
    model: str,
    prompt: Any,
    completion: Any,
    metadata: Optional[dict] = None,
) -> None:
    """Log one LLM call as a Langfuse generation span (model, I/O, metadata)."""
    if trace is None:
        return
    try:
        trace.generation(
            name=name, model=model, input=prompt, output=completion,
            metadata=metadata or {},
        )
    except Exception:
        pass


def log_span(
    trace: Any,
    name: str,
    input_data: Any = None,
    output_data: Any = None,
    metadata: Optional[dict] = None,
) -> None:
    """Log a non-LLM step (e.g. the deterministic classifier gate) as a span."""
    if trace is None:
        return
    try:
        trace.span(
            name=name, input=input_data, output=output_data, metadata=metadata or {}
        ).end()
    except Exception:
        pass


def score(trace: Any, name: str, value: float, comment: Optional[str] = None) -> None:
    """Attach a numeric score to a trace (e.g. final posture_score)."""
    if trace is None:
        return
    try:
        trace.score(name=name, value=value, comment=comment)
    except Exception:
        pass


def flush() -> None:
    client = _client()
    if client:
        try:
            client.flush()
        except Exception:
            pass
