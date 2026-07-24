"""Stock news analysis via StreamlineLLM (local)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai.streamline_llm import llm
from data.news_data import NEWS_CATEGORIES, fetch_company_news
from data.stock_data import fetch_stock_quote


@dataclass
class NewsItem:
    title: str
    summary: str
    source: str


@dataclass
class NewsAnalysis:
    ticker: str
    company_name: str
    summary: str
    sentiment_score: int
    sentiment_reasoning: str
    categories: dict[str, list[NewsItem]] = field(default_factory=dict)


def _parse_categories(payload: dict[str, Any]) -> dict[str, list[NewsItem]]:
    categories: dict[str, list[NewsItem]] = {name: [] for name in NEWS_CATEGORIES}
    raw_categories = payload.get("categories") or {}

    for name in NEWS_CATEGORIES:
        items = raw_categories.get(name) or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            categories[name].append(
                NewsItem(
                    title=title,
                    summary=str(item.get("summary", "")).strip(),
                    source=str(item.get("source", "Unknown")).strip() or "Unknown",
                )
            )
    return categories


def analyze_stock_news(ticker: str) -> NewsAnalysis:
    """Summarize and categorize recent news for a stock."""
    symbol = ticker.upper().strip()
    if not symbol:
        raise ValueError("Enter a ticker symbol to analyze news.")

    quote = fetch_stock_quote(symbol)
    headlines = fetch_company_news(symbol, limit=15)
    if not headlines:
        raise RuntimeError(f"No recent news found for '{symbol}'.")

    payload = llm.analyze_stock_news(
        {
            "ticker": symbol,
            "company_name": quote.company_name,
            "headlines": headlines,
        }
    )

    score = int(payload.get("sentiment_score", 0))
    score = max(-100, min(100, score))
    reasoning = str(payload.get("sentiment_reasoning", "")).strip()
    summary = str(payload.get("summary", "")).strip()
    if not summary or not reasoning:
        raise RuntimeError("The local news analysis was incomplete.")

    return NewsAnalysis(
        ticker=symbol,
        company_name=quote.company_name,
        summary=summary,
        sentiment_score=score,
        sentiment_reasoning=reasoning,
        categories=_parse_categories(payload),
    )
