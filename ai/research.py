"""AI-powered investment research via StreamlineLLM (local)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.context import build_research_context, extract_ticker
from ai.streamline_llm import llm


@dataclass
class ResearchResult:
    """Structured AI research response."""

    query: str
    primary_ticker: str | None
    recommendation: str
    confidence_score: int
    technical_reasoning: str
    fundamental_reasoning: str
    news_impact: str
    risks: list[str]
    investment_horizon: str
    important_uncertainties: list[str]
    profile_fit: str
    summary: str


def _parse_response(query: str, payload: dict[str, Any]) -> ResearchResult:
    risks = payload.get("risks") or []
    uncertainties = payload.get("important_uncertainties") or []
    if isinstance(risks, str):
        risks = [risks]
    if isinstance(uncertainties, str):
        uncertainties = [uncertainties]

    confidence = int(payload.get("confidence_score", 0))
    confidence = max(0, min(100, confidence))

    return ResearchResult(
        query=query,
        primary_ticker=payload.get("primary_ticker") or extract_ticker(query),
        recommendation=str(payload.get("recommendation", "Watchlist")),
        confidence_score=confidence,
        technical_reasoning=str(payload.get("technical_reasoning", "")).strip(),
        fundamental_reasoning=str(payload.get("fundamental_reasoning", "")).strip(),
        news_impact=str(payload.get("news_impact", "")).strip(),
        risks=[str(item).strip() for item in risks if str(item).strip()],
        investment_horizon=str(payload.get("investment_horizon", "")).strip(),
        important_uncertainties=[str(item).strip() for item in uncertainties if str(item).strip()],
        profile_fit=str(payload.get("profile_fit", "")).strip(),
        summary=str(payload.get("summary", "")).strip(),
    )


def run_research(query: str) -> tuple[ResearchResult, dict[str, Any]]:
    """Run investment research through the local StreamlineLLM."""
    if not query.strip():
        raise ValueError("Enter a question to research.")

    context = build_research_context(query)
    payload = llm.research(context)
    result = _parse_response(query, payload)

    if not result.primary_ticker and context.get("ticker"):
        result.primary_ticker = context["ticker"]

    _validate_result(result)
    return result, context


def _validate_result(result: ResearchResult) -> None:
    """Ensure the model returned a fully explained response."""
    required_fields = {
        "technical_reasoning": result.technical_reasoning,
        "fundamental_reasoning": result.fundamental_reasoning,
        "news_impact": result.news_impact,
        "investment_horizon": result.investment_horizon,
        "profile_fit": result.profile_fit,
        "summary": result.summary,
        "recommendation": result.recommendation,
    }
    missing = [name for name, value in required_fields.items() if not str(value).strip()]
    if missing:
        raise RuntimeError(
            "The AI response was incomplete. Missing explanations for: "
            + ", ".join(missing)
        )
    if len(result.risks) < 1 or len(result.important_uncertainties) < 1:
        raise RuntimeError("The AI response did not include enough risks or uncertainties.")
