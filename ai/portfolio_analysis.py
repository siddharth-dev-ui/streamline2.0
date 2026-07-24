"""Portfolio diversification suggestions via StreamlineLLM (local)."""

from __future__ import annotations

from dataclasses import dataclass, field

from ai.streamline_llm import llm
from data.profile_store import load_profile
from portfolio.analytics import PortfolioAnalytics


@dataclass
class DiversificationSuggestion:
    title: str
    rationale: str


@dataclass
class PortfolioDiversificationAdvice:
    summary: str
    suggestions: list[DiversificationSuggestion] = field(default_factory=list)


def suggest_diversification_improvements(analytics: PortfolioAnalytics) -> PortfolioDiversificationAdvice:
    """Generate diversification suggestions with StreamlineLLM."""
    profile = load_profile()
    payload = llm.portfolio_advice({"analytics": analytics, "profile": profile})

    summary = str(payload.get("summary", "")).strip()
    if not summary:
        raise RuntimeError("The diversification advice was incomplete.")

    suggestions: list[DiversificationSuggestion] = []
    for item in payload.get("suggestions") or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        rationale = str(item.get("rationale", "")).strip()
        if title and rationale:
            suggestions.append(DiversificationSuggestion(title=title, rationale=rationale))

    if not suggestions:
        raise RuntimeError("No diversification suggestions were returned.")

    return PortfolioDiversificationAdvice(summary=summary, suggestions=suggestions)
