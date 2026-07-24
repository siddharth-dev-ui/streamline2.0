"""Latest news curation via StreamlineLLM (local)."""

from __future__ import annotations

from dataclasses import dataclass, field

from data.latest_news import fetch_latest_news_pool


@dataclass
class LatestStory:
    title: str
    summary: str
    impact: str
    why_it_matters: str
    related_tickers: list[str] = field(default_factory=list)
    source: str = ""
    url: str = ""
    image: str = ""
    published: str = ""


@dataclass
class LatestBriefing:
    briefing: str
    stories: list[LatestStory]
    portfolio_tickers: list[str]


def _match_from_pool(title: str, pool: list[dict]) -> dict:
    needle = title.lower().strip()
    for article in pool:
        article_title = str(article.get("title", "")).lower().strip()
        if article_title == needle or needle in article_title or article_title in needle:
            return article
    return {}


def briefing_from_pool(
    pool: list[dict],
    portfolio_tickers: list[str],
    *,
    max_stories: int = 8,
) -> LatestBriefing:
    """Build a fast briefing from RSS alone (no local LLM wait)."""
    stories: list[LatestStory] = []
    for article in pool[:max_stories]:
        related = []
        related_ticker = article.get("related_ticker")
        if related_ticker:
            related = [str(related_ticker).upper()]
        stories.append(
            LatestStory(
                title=str(article.get("title", "")).strip(),
                summary=str(article.get("summary", "")).strip(),
                impact="Medium",
                why_it_matters="",
                related_tickers=related,
                source=str(article.get("publisher", "News")).strip() or "News",
                url=str(article.get("url", "")).strip(),
                image=str(article.get("image", "")).strip(),
                published=str(article.get("published", "")).strip(),
            )
        )
        if not stories[-1].title:
            stories.pop()

    if not stories:
        raise RuntimeError("No latest headlines could be loaded right now.")

    if portfolio_tickers:
        focus = ", ".join(portfolio_tickers[:6])
        briefing = (
            f"Latest market and world headlines, with extra focus on your holdings "
            f"({focus})."
        )
    else:
        briefing = (
            "Latest market and world headlines. Add portfolio holdings to personalize "
            "this briefing further."
        )

    return LatestBriefing(
        briefing=briefing,
        stories=stories,
        portfolio_tickers=portfolio_tickers,
    )


def curate_latest_news(*, use_llm: bool = True) -> LatestBriefing:
    """Fetch latest headlines; optionally rank with StreamlineLLM."""
    pool, portfolio_tickers = fetch_latest_news_pool()
    if not pool:
        raise RuntimeError("No latest headlines could be loaded right now.")

    if not use_llm:
        return briefing_from_pool(pool, portfolio_tickers)

    try:
        from ai.streamline_llm import llm

        payload = llm.curate_latest_news(
            {
                "articles": pool,
                "portfolio_tickers": portfolio_tickers,
            }
        )
    except Exception:
        return briefing_from_pool(pool, portfolio_tickers)

    briefing = str(payload.get("briefing", "")).strip()
    if not briefing:
        return briefing_from_pool(pool, portfolio_tickers)

    stories: list[LatestStory] = []
    for item in payload.get("stories") or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        related = item.get("related_tickers") or []
        if isinstance(related, str):
            related = [related]

        matched = _match_from_pool(title, pool)
        stories.append(
            LatestStory(
                title=title,
                summary=str(item.get("summary", "")).strip() or str(matched.get("summary", "")).strip(),
                impact=str(item.get("impact", "Medium")).strip().title() or "Medium",
                why_it_matters=str(item.get("why_it_matters", "")).strip(),
                related_tickers=[str(ticker).upper().strip() for ticker in related if str(ticker).strip()],
                source=str(item.get("source", "")).strip()
                or str(matched.get("publisher", "News")).strip()
                or "News",
                url=str(item.get("url", "")).strip() or str(matched.get("url", "")).strip(),
                image=str(item.get("image", "")).strip() or str(matched.get("image", "")).strip(),
                published=str(item.get("published", "")).strip()
                or str(matched.get("published", "")).strip(),
            )
        )

    if not stories:
        return briefing_from_pool(pool, portfolio_tickers)

    return LatestBriefing(
        briefing=briefing,
        stories=stories,
        portfolio_tickers=portfolio_tickers,
    )
