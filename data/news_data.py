"""News fetching and formatting."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yfinance as yf

NEWS_CATEGORIES = [
    "Earnings",
    "Analyst actions",
    "SEC filings",
    "Industry news",
    "Macroeconomic events",
]


def _parse_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d")
        if isinstance(value, str) and value:
            return value[:10]
    except (OSError, OverflowError, ValueError):
        return None
    return None


def fetch_company_news(ticker: str, limit: int = 15) -> list[dict[str, Any]]:
    """Fetch recent headlines for a ticker."""
    symbol = ticker.upper().strip()
    stock = yf.Ticker(symbol)
    articles = stock.news or []

    headlines: list[dict[str, Any]] = []
    for article in articles[:limit]:
        content = article.get("content", article)
        title = content.get("title") or article.get("title")
        if not title:
            continue

        headlines.append(
            {
                "title": title,
                "publisher": content.get("provider", {}).get("displayName")
                or article.get("publisher", "Unknown"),
                "summary": content.get("summary") or article.get("summary", ""),
                "published": _parse_timestamp(content.get("pubDate") or article.get("providerPublishTime")),
                "url": content.get("canonicalUrl") or content.get("clickThroughUrl") or article.get("link", ""),
            }
        )
    return headlines


def summarize_news_for_prompt(headlines: list[dict[str, Any]]) -> str:
    """Format headlines for the AI prompt."""
    if not headlines:
        return "No recent headlines were available for this ticker."

    lines = []
    for index, item in enumerate(headlines, start=1):
        publisher = item.get("publisher", "Unknown")
        title = item.get("title", "")
        summary = item.get("summary", "")
        published = item.get("published", "Unknown date")
        snippet = f"[{index}] {title} ({publisher}, {published})"
        if summary:
            snippet += f" — {summary[:220]}"
        lines.append(snippet)
    return "\n".join(lines)
