"""Fundamental analysis UI."""

from __future__ import annotations

import streamlit as st

from analysis.fundamental import METRIC_EXPLANATIONS, FundamentalMetrics
from data.stock_data import format_large_number, format_percent


def _fmt_ratio(value: float | None, suffix: str = "x") -> str:
    if value is None:
        return "—"
    return f"{value:.2f}{suffix}"


def render_fundamental_analysis(metrics: FundamentalMetrics) -> None:
    """Render fundamental metrics and beginner-friendly explanations."""
    st.markdown("#### Fundamental snapshot")
    st.caption("Educational context only — not investment advice.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue growth", format_percent(metrics.revenue_growth, signed=True))
    c2.metric("Earnings growth", format_percent(metrics.earnings_growth, signed=True))
    c3.metric("Free cash flow", format_large_number(int(metrics.free_cash_flow)) if metrics.free_cash_flow else "—")
    c4.metric("Total debt", format_large_number(int(metrics.total_debt)) if metrics.total_debt else "—")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Gross margin", format_percent(metrics.gross_margin))
    c6.metric("Operating margin", format_percent(metrics.operating_margin))
    c7.metric("Net margin", format_percent(metrics.net_margin))
    c8.metric("ROE", format_percent(metrics.roe))

    c9, c10, c11, c12, c13 = st.columns(5)
    c9.metric("ROIC", format_percent(metrics.roic))
    c10.metric("P/E", _fmt_ratio(metrics.pe_ratio))
    c11.metric("Forward P/E", _fmt_ratio(metrics.forward_pe))
    c12.metric("P/S", _fmt_ratio(metrics.price_to_sales))
    c13.metric("P/B", _fmt_ratio(metrics.price_to_book))

    st.metric("EV / EBITDA", _fmt_ratio(metrics.ev_to_ebitda))

    st.markdown("#### What these metrics mean")

    metric_map = {
        "Revenue growth": metrics.revenue_growth,
        "Earnings growth": metrics.earnings_growth,
        "Free cash flow": metrics.free_cash_flow,
        "Debt": metrics.total_debt,
        "Gross margin": metrics.gross_margin,
        "Operating margin": metrics.operating_margin,
        "Net margin": metrics.net_margin,
        "ROE": metrics.roe,
        "ROIC": metrics.roic,
        "P/E ratio": metrics.pe_ratio,
        "Forward P/E": metrics.forward_pe,
        "Price / Sales": metrics.price_to_sales,
        "Price / Book": metrics.price_to_book,
        "EV / EBITDA": metrics.ev_to_ebitda,
    }

    for title, explanation in METRIC_EXPLANATIONS.items():
        value = metric_map.get(title)
        label = title
        if title == "Debt":
            display = format_large_number(int(value)) if value else "—"
        elif title in {"P/E ratio", "Forward P/E", "Price / Sales", "Price / Book", "EV / EBITDA"}:
            display = _fmt_ratio(value)
        elif title == "Free cash flow":
            display = format_large_number(int(value)) if value else "—"
        elif value is not None and (
            title.endswith("growth") or title.endswith("margin") or title in {"ROE", "ROIC"}
        ):
            display = format_percent(value, signed=title.endswith("growth"))
        else:
            display = "—"

        with st.expander(f"{label} — {display}"):
            st.markdown(explanation)
