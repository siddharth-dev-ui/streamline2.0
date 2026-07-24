"""Build research context for the AI model."""

from __future__ import annotations

import re
from typing import Any

from analysis.fundamental import fetch_fundamental_metrics
from analysis.technical import compute_indicators, latest_snapshot
from data.news_data import fetch_company_news, summarize_news_for_prompt
from ai.profile_guidance import build_adaptation_guidance
from data.profile_store import load_profile
from data.stock_data import fetch_price_history, fetch_stock_quote
from portfolio.profile import generate_profile_summary

TICKER_STOPWORDS = {
    "A",
    "AI",
    "ALL",
    "AN",
    "AND",
    "ARE",
    "AS",
    "AT",
    "BE",
    "BUT",
    "BY",
    "CAN",
    "DO",
    "ETF",
    "FOR",
    "FROM",
    "HAS",
    "HAVE",
    "HOW",
    "I",
    "IF",
    "IN",
    "IS",
    "IT",
    "ITS",
    "ME",
    "MY",
    "NOT",
    "OF",
    "ON",
    "OR",
    "OUR",
    "OUT",
    "ROI",
    "RSI",
    "THE",
    "TO",
    "UP",
    "US",
    "VS",
    "WE",
    "WHAT",
    "WHEN",
    "WHO",
    "WHY",
    "WITH",
    "YOU",
    "YOUR",
}


def extract_ticker(query: str) -> str | None:
    """Extract a likely ticker symbol from a natural-language question."""
    dollar_matches = re.findall(r"\$([A-Za-z]{1,5})\b", query)
    if dollar_matches:
        return dollar_matches[0].upper()

    upper_matches = re.findall(r"\b([A-Z]{1,5})\b", query)
    for match in upper_matches:
        if match not in TICKER_STOPWORDS:
            return match

    title_matches = re.findall(r"\(([A-Za-z]{1,5})\)", query)
    for match in title_matches:
        if match.upper() not in TICKER_STOPWORDS:
            return match.upper()

    return None


def build_research_context(query: str) -> dict[str, Any]:
    """Gather user, market, technical, fundamental, and news context."""
    profile = load_profile()
    ticker = extract_ticker(query)
    context: dict[str, Any] = {
        "query": query,
        "ticker": ticker,
        "user_profile": {
            "investment_goal": profile.get("investment_goal"),
            "risk_tolerance": profile.get("risk_tolerance"),
            "investment_horizon": profile.get("investment_horizon"),
            "experience": profile.get("experience"),
            "preferred_sectors": profile.get("preferred_sectors") or [],
            "interest_in_etfs": profile.get("interest_in_etfs"),
            "interest_in_dividends": profile.get("interest_in_dividends"),
            "portfolio_size": profile.get("portfolio_size"),
        },
        "user_profile_summary": generate_profile_summary(profile),
        "adaptation_guidance": build_adaptation_guidance(profile),
        "quote": None,
        "technical": None,
        "fundamentals": None,
        "news_summary": "No ticker identified, so company-specific news was not loaded.",
    }

    if not ticker:
        return context

    quote = fetch_stock_quote(ticker)
    history = fetch_price_history(ticker, "2y")
    indicators = compute_indicators(history)
    technical = latest_snapshot(indicators)
    fundamentals = fetch_fundamental_metrics(ticker)
    news = fetch_company_news(ticker)

    context["quote"] = quote
    context["technical"] = technical
    context["fundamentals"] = fundamentals
    context["news_summary"] = summarize_news_for_prompt(news)
    return context


def context_to_prompt(context: dict[str, Any]) -> str:
    """Serialize gathered context for the model."""
    profile = context.get("user_profile") or {}
    lines = [
        f"User question: {context['query']}",
        "",
        "Investor profile summary:",
        context["user_profile_summary"],
        "",
        "Investor profile fields:",
        f"- Goal: {profile.get('investment_goal')}",
        f"- Risk tolerance: {profile.get('risk_tolerance')}",
        f"- Horizon: {profile.get('investment_horizon')}",
        f"- Experience: {profile.get('experience')}",
        f"- Preferred sectors: {', '.join(profile.get('preferred_sectors') or []) or 'None specified'}",
        f"- Interested in ETFs: {profile.get('interest_in_etfs')}",
        f"- Interested in dividends: {profile.get('interest_in_dividends')}",
        f"- Portfolio size: {profile.get('portfolio_size')}",
        "",
        "Adaptation guidance:",
        context.get("adaptation_guidance") or "Personalize the answer to the investor profile.",
    ]

    quote = context.get("quote")
    if quote:
        lines.extend(
            [
                "",
                f"Company: {quote.company_name} ({quote.ticker})",
                f"Current price: {quote.current_price}",
                f"Daily change %: {quote.daily_change_pct}",
                f"Market cap: {quote.market_cap}",
                f"P/E: {quote.pe_ratio}",
                f"52-week high: {quote.fifty_two_week_high}",
                f"52-week low: {quote.fifty_two_week_low}",
            ]
        )

    technical = context.get("technical")
    if technical:
        lines.extend(
            [
                "",
                "Technical snapshot:",
                f"RSI: {technical.rsi}",
                f"MACD: {technical.macd}",
                f"MACD signal: {technical.macd_signal}",
                f"SMA 50: {technical.sma_50}",
                f"SMA 200: {technical.sma_200}",
                f"EMA 20: {technical.ema_20}",
                f"Bollinger upper: {technical.bb_upper}",
                f"Bollinger lower: {technical.bb_lower}",
                f"ATR: {technical.atr}",
                f"Volume trend ratio: {technical.volume_trend}",
            ]
        )

    fundamentals = context.get("fundamentals")
    if fundamentals:
        lines.extend(
            [
                "",
                "Fundamental snapshot:",
                f"Revenue growth %: {fundamentals.revenue_growth}",
                f"Earnings growth %: {fundamentals.earnings_growth}",
                f"Free cash flow: {fundamentals.free_cash_flow}",
                f"Total debt: {fundamentals.total_debt}",
                f"Gross margin %: {fundamentals.gross_margin}",
                f"Operating margin %: {fundamentals.operating_margin}",
                f"Net margin %: {fundamentals.net_margin}",
                f"ROE %: {fundamentals.roe}",
                f"ROIC %: {fundamentals.roic}",
                f"P/E: {fundamentals.pe_ratio}",
                f"Forward P/E: {fundamentals.forward_pe}",
                f"P/S: {fundamentals.price_to_sales}",
                f"P/B: {fundamentals.price_to_book}",
                f"EV/EBITDA: {fundamentals.ev_to_ebitda}",
            ]
        )

    lines.extend(["", "Recent news:", context["news_summary"]])
    return "\n".join(lines)
