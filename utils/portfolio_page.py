"""Portfolio page with holdings, allocation, and diversification insights."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from ai.portfolio_analysis import PortfolioDiversificationAdvice, suggest_diversification_improvements
from data.portfolio_store import add_holding, load_holdings, remove_holding
from data.stock_data import format_currency, format_percent
from portfolio.analytics import PortfolioAnalytics, analyze_portfolio
from utils.theme import FONT_FAMILY, get_theme
from utils.table import render_themed_table


@st.cache_data(ttl=300, show_spinner=False)
def _cached_portfolio_analytics(holdings_key: tuple[tuple[str, float, float], ...]) -> PortfolioAnalytics:
    holdings = [
        {"ticker": ticker, "shares": shares, "avg_cost": avg_cost}
        for ticker, shares, avg_cost in holdings_key
    ]
    return analyze_portfolio(holdings)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_diversification_advice(holdings_key: tuple[tuple[str, float, float], ...]) -> PortfolioDiversificationAdvice:
    analytics = _cached_portfolio_analytics(holdings_key)
    return suggest_diversification_improvements(analytics)


def _clear_portfolio_caches() -> None:
    _cached_portfolio_analytics.clear()
    _cached_diversification_advice.clear()


def _holdings_key(holdings: list[dict]) -> tuple[tuple[str, float, float], ...]:
    return tuple(
        (item["ticker"], float(item["shares"]), float(item["avg_cost"]))
        for item in sorted(holdings, key=lambda holding: holding["ticker"])
    )


def _risk_label(score: int) -> str:
    if score < 35:
        return "Low"
    if score < 65:
        return "Moderate"
    return "High"


def _allocation_chart(analytics: PortfolioAnalytics) -> go.Figure:
    theme = get_theme()
    labels = list(analytics.allocation.keys())
    values = list(analytics.allocation.values())
    colors = theme["chart"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker=dict(colors=[colors[index % len(colors)] for index in range(len(labels))]),
                textinfo="label+percent",
                textfont=dict(color=theme["text"]),
                hovertemplate="%{label}<br>%{percent}<br>%{value:.1f}%<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        height=360,
        margin=dict(l=0, r=0, t=12, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["text"], family=FONT_FAMILY),
        showlegend=False,
    )
    return fig


def _sector_chart(analytics: PortfolioAnalytics) -> go.Figure:
    theme = get_theme()
    sectors = list(analytics.sector_weights.keys())
    weights = list(analytics.sector_weights.values())

    fig = go.Figure(
        data=[
            go.Bar(
                x=sectors,
                y=weights,
                marker_color=theme["accent"],
                text=[f"{weight:.1f}%" for weight in weights],
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        height=360,
        margin=dict(l=0, r=0, t=12, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["text"], family=FONT_FAMILY),
        xaxis=dict(
            title=None,
            tickfont=dict(color=theme["text_muted"]),
            linecolor=theme["border"],
        ),
        yaxis=dict(
            title="Weight (%)",
            tickfont=dict(color=theme["text_muted"]),
            gridcolor=theme["border"],
            linecolor=theme["border"],
        ),
    )
    return fig


def _render_holdings_table(holdings: list[dict], analytics: PortfolioAnalytics | None) -> None:
    if not holdings:
        theme = get_theme()
        st.markdown(
            f"""
            <div class="sl-empty-note" style="
                background:{theme["bg_secondary"]};
                color:{theme["text"]};
                border:1px solid {theme["border"]};
                border-radius:14px;
                padding:1rem 1.1rem;
                margin:0.35rem 0 1rem;
                box-shadow:{theme["btn_shadow"]};
                font-family:{FONT_FAMILY};
            ">
              No holdings yet. Add a position below to start tracking your portfolio.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    position_map = {position.ticker: position for position in analytics.positions} if analytics else {}
    rows = []
    for holding in holdings:
        position = position_map.get(holding["ticker"])
        rows.append(
            {
                "Ticker": holding["ticker"],
                "Shares": holding["shares"],
                "Avg cost": format_currency(holding["avg_cost"]),
                "Price": format_currency(position.current_price) if position else "—",
                "Value": format_currency(position.market_value) if position else "—",
                "Return": format_percent(position.return_pct, signed=True) if position else "—",
                "Weight": f"{position.weight:.1f}%" if position else "—",
                "Sector": position.sector if position else "—",
            }
        )

    render_themed_table(rows, max_height=360)

    remove_col, _ = st.columns([1, 3])
    with remove_col:
        ticker_to_remove = st.selectbox(
            "Remove holding",
            options=[holding["ticker"] for holding in holdings],
            key="portfolio_remove_ticker",
        )
        if st.button("Remove selected", key="portfolio_remove_button", use_container_width=True):
            remove_holding(ticker_to_remove)
            _clear_portfolio_caches()
            st.rerun()


@st.cache_data(ttl=120, show_spinner=False)
def _cached_ticker_price(ticker: str) -> float | None:
    """Return the latest price for a ticker, or None if lookup fails."""
    symbol = (ticker or "").strip().upper()
    if not symbol or not symbol.replace(".", "").replace("-", "").isalnum():
        return None
    try:
        from data.stock_data import fetch_stock_quote

        return fetch_stock_quote(symbol).current_price
    except Exception:
        return None


def _render_add_holding_form() -> None:
    with st.expander("Add or update holding", expanded=not load_holdings()):
        ticker = st.text_input(
            "Ticker",
            placeholder="e.g. AAPL",
            key="portfolio_ticker_input",
        )
        symbol = (ticker or "").strip().upper()
        live_price = _cached_ticker_price(symbol) if len(symbol) >= 1 else None

        # Auto-fill average cost whenever the resolved live price changes.
        if live_price is not None:
            prev_symbol = st.session_state.get("portfolio_price_for")
            prev_price = st.session_state.get("portfolio_price_value")
            if prev_symbol != symbol or prev_price != live_price:
                st.session_state["portfolio_avg_cost"] = float(live_price)
                st.session_state["portfolio_price_for"] = symbol
                st.session_state["portfolio_price_value"] = float(live_price)

        if symbol and live_price is not None:
            st.metric("Live price", format_currency(live_price))
            st.caption("Average cost was auto-filled from this price — edit it if your cost basis differs.")
        elif symbol:
            st.caption("Couldn’t fetch a live price for that ticker yet. Check the symbol and try again.")

        # Start empty (no 0.0000 placeholder). Migrate stale zero defaults once.
        if "portfolio_shares" not in st.session_state or (
            st.session_state.get("portfolio_shares") == 0.0
            and not st.session_state.get("_portfolio_shares_cleared")
        ):
            st.session_state.portfolio_shares = None
            st.session_state._portfolio_shares_cleared = True
        if "portfolio_avg_cost" not in st.session_state or (
            st.session_state.get("portfolio_avg_cost") == 0.0
            and not st.session_state.get("_portfolio_avg_cleared")
            and not st.session_state.get("portfolio_price_for")
        ):
            st.session_state.portfolio_avg_cost = None
            st.session_state._portfolio_avg_cleared = True

        shares = st.number_input(
            "Shares",
            min_value=0.0,
            step=1.0,
            format="%.4f",
            placeholder="e.g. 10",
            key="portfolio_shares",
        )
        avg_cost = st.number_input(
            "Average cost per share ($)",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            placeholder="Auto-fills from live price",
            key="portfolio_avg_cost",
        )

        if st.button("Save holding", type="primary", use_container_width=True, key="portfolio_save"):
            if shares is None or avg_cost is None:
                st.warning("Enter both shares and average cost before saving.")
            else:
                try:
                    add_holding(symbol or ticker, shares, avg_cost)
                    _clear_portfolio_caches()
                    st.session_state.portfolio_flash = f"Saved {symbol or ticker.upper().strip()}."
                    for key in (
                        "portfolio_ticker_input",
                        "portfolio_shares",
                        "portfolio_avg_cost",
                        "portfolio_price_for",
                        "portfolio_price_value",
                    ):
                        st.session_state.pop(key, None)
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))


def _render_diversification_advice(holdings_key: tuple[tuple[str, float, float], ...]) -> None:
    st.markdown("#### Diversification suggestions")
    st.caption("Educational analysis only — not investment advice.")

    if st.button("Generate suggestions", key="portfolio_suggestions_button", use_container_width=False):
        st.session_state.portfolio_fetch_suggestions = True

    if not st.session_state.get("portfolio_fetch_suggestions"):
        st.caption("Click generate to analyze diversification opportunities with AI.")
        return

    try:
        with st.spinner("Generating diversification suggestions…"):
            advice = _cached_diversification_advice(holdings_key)
    except RuntimeError as exc:
        st.error(str(exc))
        return
    except Exception:
        st.error("Unable to generate suggestions right now. Try again in a moment.")
        return

    st.write(advice.summary)
    for index, suggestion in enumerate(advice.suggestions, start=1):
        st.markdown(f"**{index}. {suggestion.title}**")
        st.write(suggestion.rationale)


def render_portfolio() -> None:
    """Render the portfolio page."""
    st.markdown(
        """
        <div class="page-header">
            <div class="page-title">portfolio</div>
            <div class="page-subtitle">Track holdings, allocation, sector exposure, returns, and risk.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    flash = st.session_state.pop("portfolio_flash", None)
    if flash:
        st.success(flash)

    holdings = load_holdings()
    _render_add_holding_form()
    st.markdown("#### Holdings")

    analytics: PortfolioAnalytics | None = None
    holdings_key = _holdings_key(holdings)

    if holdings:
        try:
            with st.spinner("Analyzing portfolio…"):
                analytics = _cached_portfolio_analytics(holdings_key)
        except ValueError as exc:
            st.warning(str(exc))
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Unable to analyze the portfolio right now. Try again shortly.")

    _render_holdings_table(holdings, analytics)

    if not analytics:
        return

    st.markdown("#### Overview")
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Total value", format_currency(analytics.total_value))
    with metric_cols[1]:
        st.metric(
            "Total return",
            format_percent(analytics.total_return_pct, signed=True),
            delta=format_currency(analytics.total_return_amount),
        )
    with metric_cols[2]:
        st.metric("Risk score", f"{analytics.risk_score}/100")
        st.caption(_risk_label(analytics.risk_score))
    with metric_cols[3]:
        st.metric("Holdings", str(len(analytics.positions)))

    st.markdown("#### Risk reasoning")
    st.markdown(analytics.risk_reasoning)

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.markdown("#### Allocation")
        st.plotly_chart(_allocation_chart(analytics), use_container_width=True)
    with chart_right:
        st.markdown("#### Sector diversification")
        st.plotly_chart(_sector_chart(analytics), use_container_width=True)

    _render_diversification_advice(holdings_key)
