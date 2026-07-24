"""Price charts for AI research responses."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from data.stock_data import StockLookupError
from utils.charting import themed_layout
from utils.theme import get_theme

CHART_WINDOWS = {
    "1 Day": ("1d", "15m"),
    "1 Week": ("5d", "1h"),
    "1 Month": ("1mo", "1d"),
    "1 Year": ("1y", "1d"),
    "5 Years": ("5y", "1wk"),
    "All Time": ("max", "1mo"),
}


@st.cache_data(ttl=300, show_spinner=False)
def _cached_window_history(ticker: str, period: str, interval: str):
    import yfinance as yf

    history = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
    if history.empty:
        raise StockLookupError(f"No chart data found for '{ticker}' ({period}).")
    return history


def build_price_line_chart(history, title: str) -> go.Figure:
    """Build a monochrome price line chart."""
    theme = get_theme()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=history["Close"],
            mode="lines",
            name="Price",
            line=dict(color=theme["accent"], width=2),
        )
    )
    themed_layout(fig, height=380)
    fig.update_layout(title=dict(text=title, font=dict(color=theme["text"], size=14)))
    fig.update_yaxes(tickprefix="$")
    fig.update_traces(hovertemplate="%{y:$,.2f}<extra></extra>")
    return fig


def render_research_chart(ticker: str | None) -> None:
    """Render the required multi-timeframe price chart."""
    if not ticker:
        st.info("No ticker was identified for this question, so a price chart is unavailable.")
        return

    st.markdown("#### Price chart")
    window = st.radio(
        "Time frame",
        options=list(CHART_WINDOWS.keys()),
        horizontal=True,
        label_visibility="collapsed",
        key=f"research_chart_window_{ticker}",
    )
    period, interval = CHART_WINDOWS[window]

    try:
        history = _cached_window_history(ticker, period, interval)
        st.plotly_chart(
            build_price_line_chart(history, f"{ticker} — {window}"),
            use_container_width=True,
        )
    except StockLookupError as exc:
        st.error(str(exc))
    except Exception:
        st.error("Unable to load chart data for this ticker.")
