"""Markets page with stock lookup, technical, and fundamental analysis."""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import yfinance as yf

from analysis.fundamental import fetch_fundamental_metrics
from data.common_stocks import get_commonly_traded
from data.stock_data import (
    StockLookupError,
    fetch_price_history,
    fetch_stock_quote,
    format_currency,
    format_large_number,
    format_percent,
)
from utils.fundamental_view import render_fundamental_analysis
from utils.technical_view import render_technical_analysis
from utils.table import render_themed_table
from utils.theme import FONT_FAMILY, get_theme

PERIOD_OPTIONS = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
    "Max": "max",
}


@st.cache_data(ttl=300, show_spinner=False)
def _cached_quote(ticker: str):
    return fetch_stock_quote(ticker)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_history(ticker: str, period: str):
    return fetch_price_history(ticker, period)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_fundamentals(ticker: str):
    return fetch_fundamental_metrics(ticker)


@st.cache_data(ttl=600, show_spinner=False)
def _cached_common_quotes() -> list[dict]:
    """Fetch latest prices for the commonly traded universe."""
    universe = get_commonly_traded()
    tickers = [item["ticker"] for item in universe]
    meta = {item["ticker"]: item for item in universe}
    price_map: dict[str, tuple[float | None, float | None]] = {
        ticker: (None, None) for ticker in tickers
    }

    data = yf.download(
        tickers=tickers,
        period="5d",
        group_by="ticker",
        threads=True,
        progress=False,
        auto_adjust=True,
    )

    multi_ticker = getattr(data.columns, "nlevels", 1) > 1

    for ticker in tickers:
        try:
            if multi_ticker:
                if ticker not in data.columns.get_level_values(0):
                    continue
                closes = data[ticker]["Close"].dropna()
            else:
                closes = data["Close"].dropna()

            if closes.empty:
                continue

            price = float(closes.iloc[-1])
            change_pct = None
            prior = float(closes.iloc[-2]) if len(closes) >= 2 else 0.0
            if prior:
                change_pct = ((price / prior) - 1) * 100
            price_map[ticker] = (price, change_pct)
        except Exception:
            continue

    return [
        {
            "Ticker": ticker,
            "Company": meta[ticker]["name"],
            "Sector": meta[ticker]["sector"],
            "Price": price_map[ticker][0],
            "Change %": price_map[ticker][1],
        }
        for ticker in tickers
    ]


def _build_price_chart(history, ticker: str) -> go.Figure:
    theme = get_theme()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=history["Close"],
            mode="lines",
            name="Close",
            line=dict(color=theme["accent"], width=2),
            fill="tozeroy",
            fillcolor=theme["chart_fill"],
        )
    )
    fig.update_layout(
        title=None,
        height=420,
        margin=dict(l=0, r=0, t=12, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["text"], family=FONT_FAMILY),
        xaxis=dict(
            showgrid=True,
            gridcolor=theme["border"],
            linecolor=theme["border"],
            tickfont=dict(color=theme["text_muted"]),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=theme["border"],
            linecolor=theme["border"],
            tickfont=dict(color=theme["text_muted"]),
            tickprefix="$",
        ),
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_traces(hovertemplate="%{y:$,.2f}<extra></extra>")
    return fig


def _render_change_label(change: float | None, change_pct: float | None) -> str:
    if change is None and change_pct is None:
        return "—"

    if change is not None:
        if change > 0:
            price_part = f"+${change:,.2f}"
        elif change < 0:
            price_part = f"-${abs(change):,.2f}"
        else:
            price_part = "$0.00"
    else:
        price_part = "—"

    pct_part = format_percent(change_pct, signed=True) if change_pct is not None else "—"
    return f"{price_part} ({pct_part})"


def _render_overview(quote, ticker: str) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current price", format_currency(quote.current_price))
    col2.metric("Daily change", _render_change_label(quote.daily_change, quote.daily_change_pct))
    col3.metric("Market cap", format_large_number(quote.market_cap))
    col4.metric("P/E ratio", f"{quote.pe_ratio:.2f}" if quote.pe_ratio else "—")

    col5, col6, col7 = st.columns(3)
    col5.metric("52-week high", format_currency(quote.fifty_two_week_high))
    col6.metric("52-week low", format_currency(quote.fifty_two_week_low))
    col7.metric(
        "Dividend yield",
        format_percent(quote.dividend_yield) if quote.dividend_yield is not None else "—",
    )

    st.markdown("#### Price history")
    period_label = st.selectbox(
        "Period",
        options=list(PERIOD_OPTIONS.keys()),
        index=3,
        label_visibility="collapsed",
        key=f"overview_period_{ticker}",
    )
    period = PERIOD_OPTIONS[period_label]

    try:
        history = _cached_history(ticker, period)
        st.plotly_chart(_build_price_chart(history, ticker), use_container_width=True)
    except StockLookupError as exc:
        st.error(str(exc))
    except Exception:
        st.error("Unable to load price history for this ticker.")


def _render_commonly_traded() -> None:
    st.markdown("### Commonly traded")
    st.caption("Widely followed, liquid U.S. stocks across major sectors. Click a ticker to look it up.")

    universe = get_commonly_traded()
    sectors = sorted({item["sector"] for item in universe})

    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        sector_filter = st.selectbox("Sector", options=["All sectors", *sectors], key="common_sector_filter")
    with search_col:
        search = st.text_input("Search", placeholder="Search ticker or company", key="common_stock_search")

    try:
        with st.spinner("Loading commonly traded quotes…"):
            rows = _cached_common_quotes()
    except Exception:
        rows = [
            {
                "Ticker": item["ticker"],
                "Company": item["name"],
                "Sector": item["sector"],
                "Price": None,
                "Change %": None,
            }
            for item in universe
        ]

    query = (search or "").strip().lower()
    filtered = []
    for row in rows:
        if sector_filter != "All sectors" and row["Sector"] != sector_filter:
            continue
        if query:
            haystack = f"{row['Ticker']} {row['Company']}".lower()
            if query not in haystack:
                continue
        filtered.append(row)

    display_rows = [
        {
            "Ticker": row["Ticker"],
            "Company": row["Company"],
            "Sector": row["Sector"],
            "Price": format_currency(row["Price"]) if row["Price"] is not None else "—",
            "Change %": format_percent(row["Change %"], signed=True) if row["Change %"] is not None else "—",
        }
        for row in filtered
    ]

    st.caption(f"Showing {len(display_rows)} of {len(universe)} commonly traded stocks")
    render_themed_table(display_rows, max_height=420)

    ticker_options = [row["Ticker"] for row in filtered] or [item["ticker"] for item in universe]
    pick_col, button_col = st.columns([3, 1])
    with pick_col:
        selected = st.selectbox("Open ticker", options=ticker_options, key="common_stock_pick")
    with button_col:
        st.write("")
        st.write("")
        if st.button("Look up", key="common_stock_lookup", type="primary", use_container_width=True):
            st.session_state.lookup_ticker = selected
            st.rerun()


def _render_lookup_section() -> None:
    st.markdown("### Stock lookup")

    if "lookup_ticker" not in st.session_state:
        st.session_state.lookup_ticker = ""

    with st.form("stock_lookup_form", clear_on_submit=False):
        ticker_input = st.text_input(
            "Ticker",
            placeholder="e.g. AAPL, MSFT, TSLA",
            value=st.session_state.lookup_ticker,
        )
        submitted = st.form_submit_button("Look up", type="primary", use_container_width=True)

    if submitted and ticker_input.strip():
        st.session_state.lookup_ticker = ticker_input.strip().upper()

    ticker = st.session_state.lookup_ticker
    if not ticker:
        return

    try:
        with st.spinner(f"Loading {ticker}…"):
            quote = _cached_quote(ticker)
    except StockLookupError as exc:
        st.error(str(exc))
        return
    except Exception:
        st.error(f"Unable to fetch data for '{ticker}'. Check the symbol and try again.")
        return

    st.markdown(f"#### {quote.company_name}")
    st.caption(quote.ticker)

    overview_tab, technical_tab, fundamental_tab = st.tabs(["Overview", "Technical", "Fundamental"])

    with overview_tab:
        _render_overview(quote, ticker)

    with technical_tab:
        try:
            with st.spinner("Calculating technical indicators…"):
                tech_history = _cached_history(ticker, "2y")
            render_technical_analysis(tech_history)
        except StockLookupError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Unable to compute technical analysis for this ticker.")

    with fundamental_tab:
        try:
            with st.spinner("Loading fundamental data…"):
                fundamentals = _cached_fundamentals(ticker)
            render_fundamental_analysis(fundamentals)
        except Exception:
            st.error("Unable to load fundamental data for this ticker.")


def render_markets() -> None:
    """Render the stock lookup and analysis page."""
    st.markdown(
        """
        <div class="page-header">
            <div class="page-title">markets</div>
            <div class="page-subtitle">Look up any ticker for price, technicals, and fundamentals.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_commonly_traded()
    st.markdown("---")
    _render_lookup_section()
