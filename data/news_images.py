"""Resolve article thumbnail images for the news UI."""

from __future__ import annotations

import hashlib
import re
from html import unescape
from urllib.parse import urlparse

import requests

_OG_RE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    re.IGNORECASE,
)


def _fallback_image(title: str, source: str) -> str:
    """Deterministic placeholder image keyed to the headline."""
    seed = hashlib.md5(f"{title}|{source}".encode("utf-8")).hexdigest()[:16]
    return f"https://picsum.photos/seed/{seed}/640/360"


def resolve_article_image(
    url: str,
    title: str = "",
    source: str = "",
    existing: str = "",
    *,
    fetch_og: bool = False,
) -> str:
    """
    Prefer an existing RSS image; optionally try Open Graph; else use a placeholder.

    Open Graph fetching is off by default so Home news renders quickly.
    """
    if existing and existing.startswith("http"):
        return existing

    if fetch_og and url and url.startswith("http"):
        try:
            response = requests.get(
                url,
                timeout=1.5,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; StreamlineNews/1.0)"},
            )
            html = response.text[:80000]
            match = _OG_RE.search(html) or _OG_RE_ALT.search(html)
            if match:
                image = unescape(match.group(1).strip())
                if image.startswith("//"):
                    image = "https:" + image
                if image.startswith("http"):
                    return image
        except Exception:
            pass

    return _fallback_image(title or "markets", source or "news")


def source_favicon(url: str, source: str = "") -> str:
    """Small publisher favicon for meta row."""
    host = ""
    if url:
        try:
            host = urlparse(url).netloc
        except Exception:
            host = ""
    if not host and source:
        host = re.sub(r"[^a-zA-Z0-9.-]", "", source.lower().replace(" ", "")) + ".com"
    if not host:
        host = "news.google.com"
    return f"https://www.google.com/s2/favicons?domain={host}&sz=64"
