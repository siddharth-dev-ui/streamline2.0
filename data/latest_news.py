"""Fetch high-impact latest headlines from Google News RSS."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html import unescape
import socket
from typing import Any
from urllib.parse import quote_plus

import feedparser

from data.portfolio_store import load_holdings

MACRO_FEEDS = [
    ("World", "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en"),
    ("Business", "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en"),
    (
        "Markets",
        "https://news.google.com/rss/search?q=stock+market+OR+Federal+Reserve+OR+inflation+OR+geopolitics&hl=en-US&gl=US&ceid=US:en",
    ),
]

_IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)


def _parse_published(entry: Any) -> str | None:
    try:
        if getattr(entry, "published_parsed", None):
            return datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M")
        published = getattr(entry, "published", None)
        if published:
            return str(published)[:16]
    except (TypeError, ValueError, OverflowError):
        return None
    return None


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _extract_image(entry: Any) -> str:
    """Best-effort thumbnail extraction from RSS media fields or HTML."""
    media_content = getattr(entry, "media_content", None) or []
    for item in media_content:
        url = item.get("url") if isinstance(item, dict) else getattr(item, "url", None)
        if url and str(url).startswith("http"):
            return str(url)

    media_thumb = getattr(entry, "media_thumbnail", None) or []
    for item in media_thumb:
        url = item.get("url") if isinstance(item, dict) else getattr(item, "url", None)
        if url and str(url).startswith("http"):
            return str(url)

    for link in getattr(entry, "links", []) or []:
        href = link.get("href") if isinstance(link, dict) else getattr(link, "href", None)
        rel = link.get("rel") if isinstance(link, dict) else getattr(link, "rel", None)
        link_type = link.get("type") if isinstance(link, dict) else getattr(link, "type", "")
        if href and str(href).startswith("http"):
            if rel == "enclosure" or (link_type and "image" in str(link_type)):
                return str(href)

    summary = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""
    match = _IMG_RE.search(summary)
    if match:
        return match.group(1)

    return ""


def _entry_to_article(entry: Any, source_label: str) -> dict[str, Any] | None:
    title = (getattr(entry, "title", None) or "").strip()
    if not title:
        return None

    publisher = source_label
    if getattr(entry, "source", None) and getattr(entry.source, "title", None):
        publisher = entry.source.title

    raw_summary = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""
    return {
        "title": title,
        "publisher": publisher,
        "summary": _strip_html(raw_summary),
        "published": _parse_published(entry),
        "url": getattr(entry, "link", "") or "",
        "image": _extract_image(entry),
        "source_label": source_label,
    }


def _fetch_feed(url: str, source_label: str, limit: int) -> list[dict[str, Any]]:
    previous_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(6)
    try:
        feed = feedparser.parse(url)
    finally:
        socket.setdefaulttimeout(previous_timeout)

    articles: list[dict[str, Any]] = []
    for entry in feed.entries[:limit]:
        article = _entry_to_article(entry, source_label)
        if article:
            articles.append(article)
    return articles


def fetch_macro_headlines(limit_per_feed: int = 8) -> list[dict[str, Any]]:
    """Fetch world/business/market headlines in parallel."""
    articles: list[dict[str, Any]] = []
    seen_titles: set[str] = set()

    with ThreadPoolExecutor(max_workers=len(MACRO_FEEDS)) as pool:
        futures = {
            pool.submit(_fetch_feed, url, label, limit_per_feed): label
            for label, url in MACRO_FEEDS
        }
        for future in as_completed(futures):
            try:
                batch = future.result()
            except Exception:
                continue
            for article in batch:
                key = article["title"].lower()
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                articles.append(article)
    return articles


def fetch_ticker_headlines(ticker: str, limit: int = 5) -> list[dict[str, Any]]:
    """Fetch Google News headlines for a ticker."""
    symbol = ticker.upper().strip()
    query = quote_plus(f"{symbol} stock OR shares OR earnings")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    return _fetch_feed(url, symbol, limit)


def fetch_latest_news_pool(max_articles: int = 40) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Build a pool of latest headlines from macro feeds and portfolio holdings.
    Returns (articles, portfolio_tickers).
    """
    holdings = load_holdings()
    tickers = [item["ticker"] for item in holdings]

    articles = fetch_macro_headlines(limit_per_feed=8)
    seen = {item["title"].lower() for item in articles}

    focus = tickers[:4]
    if focus:
        with ThreadPoolExecutor(max_workers=min(4, len(focus))) as pool:
            futures = {
                pool.submit(fetch_ticker_headlines, ticker, 3): ticker for ticker in focus
            }
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    batch = future.result()
                except Exception:
                    continue
                for article in batch:
                    key = article["title"].lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    article["related_ticker"] = ticker
                    articles.append(article)

    return articles[:max_articles], tickers


def format_articles_for_prompt(articles: list[dict[str, Any]]) -> str:
    """Serialize headlines for AI ranking."""
    if not articles:
        return "No headlines were available."

    lines = []
    for index, article in enumerate(articles, start=1):
        related = article.get("related_ticker")
        related_note = f", related to {related}" if related else ""
        lines.append(
            f"[{index}] {article['title']} "
            f"({article.get('publisher', 'Unknown')}, {article.get('published', 'unknown date')}"
            f"{related_note})"
        )
        summary = article.get("summary") or ""
        if summary:
            lines.append(f"    {summary[:220]}")
    return "\n".join(lines)
