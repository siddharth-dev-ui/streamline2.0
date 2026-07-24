"""Shared helpers for AI / analysis errors."""

from __future__ import annotations


def format_llm_error(exc: BaseException) -> str:
    """Turn analysis exceptions into clear user-facing messages."""
    if isinstance(exc, RuntimeError):
        return str(exc)
    if isinstance(exc, ValueError):
        return str(exc)
    return f"StreamlineLLM could not finish this request: {exc}"
