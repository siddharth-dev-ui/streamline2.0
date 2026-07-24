"""Technical analysis charts and UI."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from analysis.technical import INDICATOR_EXPLANATIONS, compute_indicators, latest_snapshot
from utils.charting import themed_layout
from utils.theme import get_theme


def build_technical_charts(data) -> go.Figure:
    """Build a multi-panel technical analysis chart."""
    theme = get_theme()
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.45, 0.2, 0.2, 0.15],
        subplot_titles=("Price & overlays", "RSI", "MACD", "Volume"),
    )

    fig.add_trace(
        go.Scatter(x=data.index, y=data["Close"], name="Close", line=dict(color=theme["accent"], width=2)),
        row=1,
        col=1,
    )
    for col_name, label in [
        ("SMA_50", "SMA 50"),
        ("SMA_200", "SMA 200"),
        ("EMA_20", "EMA 20"),
        ("BB_Upper", "BB Upper"),
        ("BB_Lower", "BB Lower"),
    ]:
        if col_name in data.columns:
            dash = "dot" if col_name.startswith("BB") else "dash"
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[col_name],
                    name=label,
                    line=dict(color=theme["text_muted"], width=1, dash=dash),
                ),
                row=1,
                col=1,
            )

    fig.add_trace(
        go.Scatter(x=data.index, y=data["RSI"], name="RSI", line=dict(color=theme["accent"], width=1.5)),
        row=2,
        col=1,
    )
    fig.add_hline(y=70, line_dash="dot", line_color=theme["border"], row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color=theme["border"], row=2, col=1)

    fig.add_trace(
        go.Scatter(x=data.index, y=data["MACD"], name="MACD", line=dict(color=theme["accent"], width=1.5)),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MACD_Signal"],
            name="Signal",
            line=dict(color=theme["text_muted"], width=1, dash="dash"),
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Bar(x=data.index, y=data["MACD_Hist"], name="Histogram", marker_color=theme["accent_muted"]),
        row=3,
        col=1,
    )

    fig.add_trace(
        go.Bar(x=data.index, y=data["Volume"], name="Volume", marker_color=theme["text_muted"], opacity=0.5),
        row=4,
        col=1,
    )
    if "Volume_SMA_20" in data.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["Volume_SMA_20"],
                name="Vol SMA 20",
                line=dict(color=theme["accent_muted"], width=1),
            ),
            row=4,
            col=1,
        )

    themed_layout(fig, height=900)
    fig.update_yaxes(tickprefix="$", row=1, col=1)
    return fig


def render_technical_analysis(data) -> None:
    """Render technical indicator summary, charts, and explanations."""
    indicators = compute_indicators(data)
    snapshot = latest_snapshot(indicators)

    st.markdown("#### Technical snapshot")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RSI (14)", f"{snapshot.rsi:.1f}" if snapshot.rsi else "—")
    c2.metric("MACD", f"{snapshot.macd:.2f}" if snapshot.macd else "—")
    c3.metric("ATR (14)", f"{snapshot.atr:.2f}" if snapshot.atr else "—")
    c4.metric(
        "Volume trend",
        f"{snapshot.volume_trend:.2f}x" if snapshot.volume_trend else "—",
        help="Ratio of 20-day average volume to 50-day average volume",
    )

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("SMA 50", f"${snapshot.sma_50:,.2f}" if snapshot.sma_50 else "—")
    c6.metric("SMA 200", f"${snapshot.sma_200:,.2f}" if snapshot.sma_200 else "—")
    c7.metric("EMA 20", f"${snapshot.ema_20:,.2f}" if snapshot.ema_20 else "—")
    c8.metric(
        "Bollinger range",
        f"${snapshot.bb_lower:,.2f} – ${snapshot.bb_upper:,.2f}"
        if snapshot.bb_lower and snapshot.bb_upper
        else "—",
    )

    st.plotly_chart(build_technical_charts(indicators), use_container_width=True)

    st.markdown("#### What these indicators mean")
    st.caption("Educational context only — not investment advice.")

    for title, explanation in INDICATOR_EXPLANATIONS.items():
        with st.expander(title):
            st.markdown(explanation)
