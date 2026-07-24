"""Watchlist page — multiple lists, stock cards, filters, and quick actions."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from data.portfolio_store import add_holding
from data.stock_data import StockLookupError, format_currency, format_large_number, format_percent
from data.watchlist_store import (
    add_ticker,
    create_watchlist,
    delete_watchlist,
    get_active_watchlist,
    list_watchlists,
    remove_ticker,
    rename_watchlist,
    set_active_watchlist,
)
from utils.theme import FONT_FAMILY, get_theme
from watchlist.quotes import WatchlistCardData, fetch_watchlist_cards, resolve_symbol

SORT_OPTIONS = {
    "Alphabetical": "alpha",
    "Price": "price",
    "Daily Change": "change",
    "Market Cap": "mcap",
}

FILTER_OPTIONS = ["All", "Gainers", "Losers"]


@st.cache_data(ttl=300, show_spinner=False)
def _cached_cards(tickers: tuple[str, ...]) -> list[WatchlistCardData]:
    return fetch_watchlist_cards(list(tickers))


def _clear_watchlist_cache() -> None:
    _cached_cards.clear()


def _sparkline(values: list[float], up: bool | None) -> go.Figure:
    theme = get_theme()
    if up is True:
        color = "#22c55e"
    elif up is False:
        color = "#ef4444"
    else:
        color = theme["accent"]

    fig = go.Figure(
        data=[
            go.Scatter(
                y=values,
                mode="lines",
                line=dict(color=color, width=2),
                fill="tozeroy",
                fillcolor="rgba(168, 85, 247, 0.12)" if up is None else (
                    "rgba(34, 197, 94, 0.12)" if up else "rgba(239, 68, 68, 0.12)"
                ),
                hoverinfo="skip",
            )
        ]
    )
    fig.update_layout(
        height=70,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def _change_color(change_pct: float | None) -> str:
    if change_pct is None:
        return get_theme()["text_muted"]
    if change_pct > 0:
        return "#22c55e"
    if change_pct < 0:
        return "#ef4444"
    return get_theme()["text_muted"]


def _filter_and_sort(
    cards: list[WatchlistCardData],
    *,
    search: str,
    sector: str,
    move_filter: str,
    sort_key: str,
) -> list[WatchlistCardData]:
    query = (search or "").strip().lower()
    filtered: list[WatchlistCardData] = []
    for card in cards:
        if query:
            hay = f"{card.ticker} {card.company_name} {card.sector}".lower()
            if query not in hay:
                continue
        if sector != "All sectors" and card.sector != sector:
            continue
        change = card.daily_change_pct
        if move_filter == "Gainers" and (change is None or change <= 0):
            continue
        if move_filter == "Losers" and (change is None or change >= 0):
            continue
        filtered.append(card)

    if sort_key == "alpha":
        filtered.sort(key=lambda card: card.company_name.lower())
    elif sort_key == "price":
        filtered.sort(key=lambda card: card.current_price or -1, reverse=True)
    elif sort_key == "change":
        filtered.sort(key=lambda card: card.daily_change_pct if card.daily_change_pct is not None else -999, reverse=True)
    elif sort_key == "mcap":
        filtered.sort(key=lambda card: card.market_cap or -1, reverse=True)
    return filtered


def _go_analyze(ticker: str) -> None:
    st.session_state.current_page = "Home"
    st.session_state.last_research_query = f"Should I buy {ticker}?"
    st.session_state.home_research_query = f"Should I buy {ticker}?"
    st.session_state.lookup_ticker = ticker
    st.session_state.watchlist_autorun_research = True
    st.rerun()


def _go_chart(ticker: str) -> None:
    st.session_state.current_page = "Markets"
    st.session_state.lookup_ticker = ticker
    st.rerun()


def _add_to_portfolio(ticker: str, price: float | None) -> None:
    avg_cost = float(price) if price and price > 0 else 1.0
    try:
        add_holding(ticker, shares=1.0, avg_cost=avg_cost)
        st.session_state.current_page = "Portfolio"
        st.session_state.portfolio_flash = f"Added {ticker} to portfolio (1 share @ {format_currency(avg_cost)})."
        st.rerun()
    except ValueError as exc:
        st.warning(str(exc))


def _render_empty_global() -> None:
    st.markdown(
        """
        <div class="watch-empty">
            <div class="watch-empty-title">Start tracking stocks you're interested in.</div>
            <div class="watch-empty-sub">Create a watchlist to follow prices, moves, and ideas.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("create_watchlist_empty_form", clear_on_submit=True):
        name = st.text_input("Watchlist name", placeholder="e.g. Tech, Dividend Stocks, ETFs")
        submitted = st.form_submit_button("Create Watchlist", type="primary", use_container_width=True)
    if submitted:
        try:
            create_watchlist(name)
            st.rerun()
        except ValueError as exc:
            st.warning(str(exc))


def _render_watchlist_toolbar(active: dict) -> None:
    lists = list_watchlists()
    names = {item["id"]: item["name"] for item in lists}
    ids = [item["id"] for item in lists]

    top_left, top_right = st.columns([2.4, 1.6])
    with top_left:
        selected = st.selectbox(
            "Active watchlist",
            options=ids,
            format_func=lambda value: names.get(value, value),
            index=ids.index(active["id"]) if active["id"] in ids else 0,
            key="watchlist_active_select",
        )
        if selected != active["id"]:
            set_active_watchlist(selected)
            st.rerun()
    with top_right:
        st.write("")
        st.write("")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("New", key="watchlist_new_toggle", use_container_width=True):
                st.session_state.watchlist_show_create = True
        with c2:
            if st.button("Rename", key="watchlist_rename_toggle", use_container_width=True):
                st.session_state.watchlist_show_rename = True
        with c3:
            if st.button("Delete", key="watchlist_delete_btn", use_container_width=True):
                delete_watchlist(active["id"])
                _clear_watchlist_cache()
                st.rerun()

    if st.session_state.get("watchlist_show_create"):
        with st.form("create_watchlist_form", clear_on_submit=True):
            name = st.text_input("New watchlist name", placeholder="e.g. Growth")
            cols = st.columns(2)
            with cols[0]:
                create = st.form_submit_button("Create", type="primary", use_container_width=True)
            with cols[1]:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
        if cancel:
            st.session_state.watchlist_show_create = False
            st.rerun()
        if create:
            try:
                create_watchlist(name)
                st.session_state.watchlist_show_create = False
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))

    if st.session_state.get("watchlist_show_rename"):
        with st.form("rename_watchlist_form", clear_on_submit=True):
            name = st.text_input("Rename watchlist", value=active["name"])
            cols = st.columns(2)
            with cols[0]:
                save = st.form_submit_button("Save name", type="primary", use_container_width=True)
            with cols[1]:
                cancel = st.form_submit_button("Cancel rename", use_container_width=True)
        if cancel:
            st.session_state.watchlist_show_rename = False
            st.rerun()
        if save:
            try:
                rename_watchlist(active["id"], name)
                st.session_state.watchlist_show_rename = False
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))


def _render_add_stock(active: dict) -> None:
    with st.form("watchlist_add_stock_form", clear_on_submit=True):
        query = st.text_input(
            "Add stock",
            placeholder="Ticker or company name (e.g. AAPL or NVIDIA)",
        )
        submitted = st.form_submit_button("Add stock", type="primary", use_container_width=True)
    if submitted:
        try:
            symbol = resolve_symbol(query)
            add_ticker(active["id"], symbol)
            _clear_watchlist_cache()
            st.success(f"Added {symbol}.")
            st.rerun()
        except (ValueError, StockLookupError) as exc:
            st.warning(str(exc))
        except Exception:
            st.error("Unable to add that stock right now.")


def _render_empty_list(active: dict) -> None:
    st.markdown(
        f"""
        <div class="watch-empty">
            <div class="watch-empty-title">{active["name"]} is empty</div>
            <div class="watch-empty-sub">Add tickers to start tracking prices and daily moves.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Add your first stock", type="primary", use_container_width=True, key="watchlist_first_stock"):
        st.session_state.watchlist_focus_add = True

    if st.session_state.get("watchlist_focus_add", True):
        _render_add_stock(active)


def _render_card(card: WatchlistCardData, watchlist_id: str) -> None:
    theme = get_theme()
    change = card.daily_change_pct
    up = None if change is None else change > 0
    change_label = format_percent(change, signed=True) if change is not None else "—"
    color = _change_color(change)

    with st.container(border=True):
        head_l, head_r = st.columns([3, 1.2])
        with head_l:
            st.markdown(f"**{card.company_name}**")
            st.caption(f"{card.ticker} · {card.sector}")
        with head_r:
            st.markdown(
                f"<div style='text-align:right;font-weight:600;color:{theme['text']}'>"
                f"{format_currency(card.current_price)}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='text-align:right;color:{color};font-weight:600'>{change_label}</div>",
                unsafe_allow_html=True,
            )

        meta_l, meta_r = st.columns([1.2, 2])
        with meta_l:
            st.caption("Market cap")
            st.write(format_large_number(card.market_cap))
        with meta_r:
            if card.sparkline and len(card.sparkline) >= 2:
                st.plotly_chart(
                    _sparkline(card.sparkline, up if change != 0 else None),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key=f"spark_{watchlist_id}_{card.ticker}",
                )
            else:
                st.caption("Sparkline unavailable")

        a1, a2, a3, a4 = st.columns(4)
        with a1:
            if st.button("Analyze", key=f"wa_analyze_{watchlist_id}_{card.ticker}", use_container_width=True):
                _go_analyze(card.ticker)
        with a2:
            if st.button("View Chart", key=f"wa_chart_{watchlist_id}_{card.ticker}", use_container_width=True):
                _go_chart(card.ticker)
        with a3:
            if st.button("Add to Portfolio", key=f"wa_port_{watchlist_id}_{card.ticker}", use_container_width=True):
                _add_to_portfolio(card.ticker, card.current_price)
        with a4:
            if st.button("Remove", key=f"wa_rm_{watchlist_id}_{card.ticker}", use_container_width=True):
                remove_ticker(watchlist_id, card.ticker)
                _clear_watchlist_cache()
                st.rerun()


def render_watchlist() -> None:
    """Render the watchlist page."""
    st.markdown(
        """
        <div class="page-header">
            <div class="page-title">watchlist</div>
            <div class="page-subtitle">Track stocks across custom lists with live prices and quick actions.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    lists = list_watchlists()
    if not lists:
        _render_empty_global()
        return

    active = get_active_watchlist()
    if not active:
        _render_empty_global()
        return

    _render_watchlist_toolbar(active)
    st.divider()

    tickers = active.get("tickers") or []
    if not tickers:
        _render_empty_list(active)
        return

    _render_add_stock(active)

    with st.spinner("Loading watchlist quotes…"):
        cards = _cached_cards(tuple(tickers))

    sectors = sorted({card.sector for card in cards if card.sector})
    search_col, sort_col, filter_col, sector_col = st.columns([1.6, 1, 1, 1.2])
    with search_col:
        search = st.text_input("Search watchlist", placeholder="Search ticker or company", key="watchlist_search")
    with sort_col:
        sort_label = st.selectbox("Sort by", options=list(SORT_OPTIONS.keys()), key="watchlist_sort")
    with filter_col:
        move_filter = st.selectbox("Move", options=FILTER_OPTIONS, key="watchlist_move_filter")
    with sector_col:
        sector = st.selectbox("Sector", options=["All sectors", *sectors], key="watchlist_sector_filter")

    visible = _filter_and_sort(
        cards,
        search=search,
        sector=sector,
        move_filter=move_filter,
        sort_key=SORT_OPTIONS[sort_label],
    )
    st.caption(f"Showing {len(visible)} of {len(cards)} stocks in {active['name']}")

    if not visible:
        st.info("No stocks match these filters.")
        return

    # Responsive: 1 col on narrow concept via sequential cards; use 2-col grid on desktop
    for index in range(0, len(visible), 2):
        cols = st.columns(2)
        for offset, col in enumerate(cols):
            if index + offset >= len(visible):
                break
            with col:
                _render_card(visible[index + offset], active["id"])
