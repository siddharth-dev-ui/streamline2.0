"""Reusable UI components for Streamline."""

from __future__ import annotations

import streamlit as st

from utils.theme import get_theme, init_theme, toggle_theme

PAGE_KEY = "current_page"
DEFAULT_PAGE = "Home"

NAV_ITEMS = [
    "Home",
    "Portfolio",
    "Watchlist",
    "Markets",
    "Settings",
]


def init_navigation() -> str:
    """Initialize the active page in session state."""
    if PAGE_KEY not in st.session_state:
        st.session_state[PAGE_KEY] = DEFAULT_PAGE
    # News tab was removed — send any stale session value home.
    if st.session_state[PAGE_KEY] == "News":
        st.session_state[PAGE_KEY] = DEFAULT_PAGE
    return st.session_state[PAGE_KEY]


def set_page(page: str) -> None:
    """Update the active page."""
    st.session_state[PAGE_KEY] = page


def render_sidebar() -> None:
    """Render the collapsible sidebar with navigation and theme toggle."""
    init_navigation()
    theme = init_theme()
    get_theme()

    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">streamline</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)

        current = st.session_state[PAGE_KEY]
        for label in NAV_ITEMS:
            is_active = label == current
            button_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{label}", type=button_type, use_container_width=True):
                set_page(label)
                st.rerun()

        st.markdown("---")

        st.markdown('<div class="sidebar-section">Appearance</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="theme-toggle-label">Mode: <strong>{theme.title()}</strong></div>',
            unsafe_allow_html=True,
        )

        toggle_label = "Light" if theme == "dark" else "Dark"
        if st.button(toggle_label, key="theme_toggle", use_container_width=True):
            toggle_theme()
            st.rerun()

        st.markdown("---")
        from utils.auth import get_current_user, logout_user

        user = get_current_user()
        if user:
            label = user.get("name") or user.get("email") or "Signed in"
            st.caption(label)
            if st.button("Sign out", key="auth_sign_out", use_container_width=True):
                logout_user()
                st.rerun()


def _run_research_query(query: str) -> None:
    from ai.research import run_research

    try:
        with st.spinner("Analyzing your question…"):
            result, _ = run_research(query)
        st.session_state.research_result = result
    except RuntimeError as exc:
        st.session_state.research_result = None
        st.error(str(exc))
    except ValueError as exc:
        st.session_state.research_result = None
        st.warning(str(exc))
    except Exception:
        st.session_state.research_result = None
        st.error("Unable to complete AI research right now. Try again in a moment.")


def render_home() -> None:
    """Render the Streamline home page with research chat and news feed."""
    from utils.loading import render_skeleton
    from utils.news_page import clear_news_caches, render_news_feed
    from utils.research_display import render_research_result

    st.markdown(
        """
        <div class="home-hero">
            <div class="logo-text">streamline</div>
            <div class="tagline">research-grade investing workspace</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="search-label">What would you like to research today?</div>',
        unsafe_allow_html=True,
    )

    if "home_research_query" not in st.session_state:
        st.session_state.home_research_query = st.session_state.get("last_research_query", "")

    with st.form("research_form", clear_on_submit=False):
        query = st.text_area(
            label="Research query",
            placeholder="Ask anything about a stock, sector, or strategy…",
            label_visibility="collapsed",
            height=75,
            key="home_research_query",
        )
        submitted = st.form_submit_button("Research", type="primary", use_container_width=True)

    if submitted and query.strip():
        st.session_state.last_research_query = query.strip()
        _run_research_query(query.strip())

    if st.session_state.pop("watchlist_autorun_research", False):
        auto_query = st.session_state.get("last_research_query", "").strip()
        if auto_query:
            st.session_state.home_research_query = auto_query
            _run_research_query(auto_query)

    ticker_candidate = (query or "").strip().upper()
    if ticker_candidate.isalpha() and 1 <= len(ticker_candidate) <= 5:
        if st.button(f"Look up {ticker_candidate} in Markets", use_container_width=True):
            st.session_state.current_page = "Markets"
            st.session_state.lookup_ticker = ticker_candidate
            st.rerun()

    if st.session_state.get("research_result"):
        render_research_result(st.session_state.research_result)

    st.markdown("### Market news")
    st.caption("Latest headlines and ticker analysis — formerly the News tab.")
    try:
        with st.spinner("Loading market news…"):
            render_news_feed(include_ticker_analysis=True)
    except Exception as exc:
        render_skeleton("News unavailable")
        st.error(f"Unable to load news right now: {exc}")
        if st.button("Retry news", key="home_retry_news"):
            clear_news_caches()
            st.rerun()


def render_placeholder(page: str) -> None:
    """Render a placeholder for pages not yet implemented."""
    st.markdown(
        f"""
        <div class="placeholder-page">
            <div class="placeholder-title">{page}</div>
            <div class="placeholder-sub">This section is coming soon.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page() -> None:
    """Render the active page content with deferred imports per route."""
    page = init_navigation()

    if page == "Home":
        render_home()
    elif page == "Markets":
        from utils.markets_page import render_markets

        render_markets()
    elif page == "Portfolio":
        from utils.portfolio_page import render_portfolio

        render_portfolio()
    elif page == "Watchlist":
        from utils.watchlist_page import render_watchlist

        render_watchlist()
    elif page == "Settings":
        from utils.settings_page import render_settings

        render_settings()
    else:
        render_placeholder(page)
