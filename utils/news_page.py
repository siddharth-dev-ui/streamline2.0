"""News page for stock-related financial headlines."""

from __future__ import annotations

import re

import streamlit as st

from ai.errors import format_llm_error
from ai.latest_news import LatestBriefing, LatestStory, curate_latest_news
from ai.news_analysis import NewsAnalysis, analyze_stock_news
from data.news_data import NEWS_CATEGORIES
from data.news_images import resolve_article_image


@st.cache_data(ttl=900, show_spinner=False)
def _cached_latest_briefing(use_llm: bool = False) -> LatestBriefing:
    return curate_latest_news(use_llm=use_llm)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_news_analysis(ticker: str) -> NewsAnalysis:
    return analyze_stock_news(ticker)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_story_image(url: str, title: str, source: str, existing: str) -> str:
    return resolve_article_image(url=url, title=title, source=source, existing=existing)


def clear_news_caches() -> None:
    """Clear only news-related caches (avoids wiping markets/watchlist)."""
    _cached_latest_briefing.clear()
    _cached_news_analysis.clear()
    _cached_story_image.clear()


def _sentiment_label(score: int) -> str:
    if score >= 35:
        return "Positive"
    if score <= -35:
        return "Negative"
    return "Neutral"


def _clean_text(value: str) -> str:
    text = " ".join((value or "").replace("\n", " ").split())
    # Never show raw URLs in article copy.
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip(" -•|")
    # Escape $ so Streamlit doesn't treat "$4 a gallon" as LaTeX (green math text).
    text = text.replace("$", r"\$")
    return text


def _headline_markdown(title: str, url: str) -> str:
    safe_title = _clean_text(title).replace("[", "(").replace("]", ")")
    return f"##### {safe_title}"


def _render_category(name: str, items) -> None:
    st.markdown(f"#### {name}")
    if not items:
        st.caption("No recent headlines matched this category.")
        return

    for item in items:
        st.markdown(f"**{_clean_text(item.title)}**")
        if item.source:
            st.caption(item.source)
        st.write(_clean_text(item.summary))


def _story_image(story: LatestStory) -> str:
    # Fast path: RSS image or placeholder — no Open Graph network wait on Home.
    return _cached_story_image(
        story.url or "",
        story.title,
        story.source or "",
        story.image or "",
    )


def _render_story_meta(story: LatestStory) -> None:
    impact = story.impact if story.impact in {"High", "Medium"} else "Medium"
    parts = [story.source or "News"]
    if story.published:
        parts.append(story.published)
    parts.append(f"{impact} impact")
    st.caption(" · ".join(parts))


def _render_hero_story(story: LatestStory) -> None:
    image = _story_image(story)
    try:
        st.image(image, use_container_width=True)
    except Exception:
        st.info("Image unavailable")

    _render_story_meta(story)
    st.markdown(_headline_markdown(story.title, story.url or ""))
    snippet = _clean_text(story.summary or story.why_it_matters or "")
    if snippet:
        st.write(snippet[:220])
    if story.related_tickers:
        st.caption("Related: " + " · ".join(story.related_tickers))


def _render_list_story(story: LatestStory, key: str) -> None:
    left, right = st.columns([3.2, 1.2])
    with left:
        _render_story_meta(story)
        st.markdown(_headline_markdown(story.title, story.url or ""))
        snippet = _clean_text(story.summary or story.why_it_matters or "")
        if snippet:
            st.caption(snippet[:160])
        if story.related_tickers:
            st.caption("Related: " + " · ".join(story.related_tickers))
    with right:
        image = _story_image(story)
        try:
            st.image(image, use_container_width=True)
        except Exception:
            st.write("")


def _render_latest_section(*, use_llm: bool | None = None) -> None:
    st.markdown("### Latest")
    st.caption("High-impact headlines tailored to markets, world events, and your portfolio.")

    if use_llm is None:
        use_llm = bool(st.session_state.get("news_use_llm", False))

    try:
        with st.spinner("Loading latest headlines…"):
            briefing = _cached_latest_briefing(use_llm=use_llm)
    except Exception as exc:
        st.error(format_llm_error(exc))
        if st.button("Retry latest news", key="retry_latest_news"):
            clear_news_caches()
            st.rerun()
        return

    if not use_llm:
        if st.button("Enhance with AI", key="enhance_news_ai"):
            st.session_state["news_use_llm"] = True
            st.rerun()

    if briefing.portfolio_tickers:
        st.caption(f"Portfolio focus: {', '.join(briefing.portfolio_tickers)}")
    else:
        st.caption(
            "No portfolio holdings yet — showing market and world headlines. "
            "Add holdings to personalize."
        )

    st.write(_clean_text(briefing.briefing))
    st.divider()

    if not briefing.stories:
        st.info("No stories available right now.")
        return

    _render_hero_story(briefing.stories[0])

    for index, story in enumerate(briefing.stories[1:], start=1):
        st.divider()
        _render_list_story(story, key=f"story_{index}")


def _render_ticker_analysis() -> None:
    st.markdown("### Stock news")
    st.caption("Analyze recent headlines for a selected ticker.")

    if "news_ticker" not in st.session_state:
        st.session_state.news_ticker = st.session_state.get("lookup_ticker", "")

    with st.form("news_lookup_form", clear_on_submit=False):
        ticker_input = st.text_input(
            "Ticker",
            placeholder="e.g. AAPL, MSFT, TSLA",
            value=st.session_state.news_ticker,
        )
        submitted = st.form_submit_button("Analyze news", type="primary", use_container_width=True)

    if submitted and ticker_input.strip():
        st.session_state.news_ticker = ticker_input.strip().upper()
        _cached_news_analysis.clear()

    ticker = st.session_state.news_ticker
    if not ticker:
        return

    try:
        with st.spinner(f"Analyzing news for {ticker}…"):
            analysis = _cached_news_analysis(ticker)
    except ValueError as exc:
        st.warning(str(exc))
        return
    except Exception as exc:
        st.error(format_llm_error(exc))
        return

    st.markdown(f"#### {analysis.company_name}")
    st.caption(analysis.ticker)

    st.markdown("##### Summary")
    st.write(analysis.summary)

    score_col, label_col = st.columns([1, 3])
    with score_col:
        st.metric("Sentiment score", f"{analysis.sentiment_score:+d}")
        st.caption(_sentiment_label(analysis.sentiment_score))
    with label_col:
        normalized = (analysis.sentiment_score + 100) / 200
        st.progress(normalized)
        st.markdown("##### Why this score?")
        st.write(analysis.sentiment_reasoning)

    st.markdown("##### Categories")
    st.caption("Educational analysis only — not investment advice.")

    tabs = st.tabs(NEWS_CATEGORIES)
    for tab, category in zip(tabs, NEWS_CATEGORIES):
        with tab:
            _render_category(category, analysis.categories.get(category, []))


def render_news_feed(*, include_ticker_analysis: bool = True) -> None:
    """Render news content for embedding (e.g. Home) without a standalone page header."""
    _render_latest_section()
    if include_ticker_analysis:
        st.divider()
        _render_ticker_analysis()


def render_news() -> None:
    """Render the standalone news analysis page."""
    st.markdown(
        """
        <div class="page-header">
            <div class="page-title">news</div>
            <div class="page-subtitle">Latest market headlines plus ticker-level sentiment analysis.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_news_feed()
