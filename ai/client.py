"""LLM provider configuration — StreamlineLLM runs fully local by default."""

from __future__ import annotations

from ai.streamline_llm import StreamlineLLM, llm

DEFAULT_MODEL = StreamlineLLM.name
DEFAULT_BASE_URL = "local://streamline-llm"


def get_model() -> str:
    return StreamlineLLM.name


def get_base_url() -> str:
    return DEFAULT_BASE_URL


def get_local_llm() -> StreamlineLLM:
    """Return the local StreamlineLLM instance."""
    return llm


def describe_config() -> dict[str, object]:
    """Status for UI — no external API key required."""
    return {
        "provider": "StreamlineLLM",
        "mode": "local",
        "model": StreamlineLLM.name,
        "version": StreamlineLLM.version,
        "key_configured": True,
        "base_url": DEFAULT_BASE_URL,
        "env_path": "n/a (local model)",
        "env_exists": True,
    }
