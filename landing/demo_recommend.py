"""Live demo recommendation engine for the Streamline landing page."""

from __future__ import annotations

import math
import re
from typing import Any

import pandas as pd
import yfinance as yf

_TICKER_RE = re.compile(r"^[A-Za-z]{1,5}(?:[.-][A-Za-z]{1,2})?$")


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return None
        return result
    except (TypeError, ValueError):
        return None


def _rsi(closes: pd.Series, period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    delta = closes.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    latest_gain = _safe_float(gain.iloc[-1])
    latest_loss = _safe_float(loss.iloc[-1])
    if latest_gain is None or latest_loss is None or latest_loss == 0:
        if latest_loss == 0 and latest_gain is not None and latest_gain > 0:
            return 100.0
        return None
    rs = latest_gain / latest_loss
    return 100 - (100 / (1 + rs))


def _normalize_ticker(raw: str) -> str:
    text = (raw or "").strip().upper()
    text = re.sub(r"^(SHOULD I BUY|BUY|ANALYZE|LOOK UP)\s+", "", text, flags=re.I)
    text = text.strip(" ?!.,")
    # Pull a plausible ticker token if the user typed a sentence.
    match = re.search(r"\b([A-Z]{1,5}(?:[.-][A-Z]{1,2})?)\b", text)
    if match:
        return match.group(1)
    return text


def build_demo_recommendation(raw_query: str) -> dict[str, Any]:
    """
    Build a transparent demo recommendation from live market data.

    Educational only — not financial advice.
    """
    ticker = _normalize_ticker(raw_query)
    if not ticker or not _TICKER_RE.match(ticker):
        raise ValueError("Enter a valid ticker symbol, e.g. MSFT, AAPL, or NVDA.")

    stock = yf.Ticker(ticker)
    info = stock.info or {}
    history = stock.history(period="6mo", interval="1d")
    if history is None or history.empty or "Close" not in history:
        raise ValueError(f"Couldn't load live market data for {ticker}. Try another symbol.")

    closes = history["Close"].dropna()
    if len(closes) < 30:
        raise ValueError(f"Not enough price history for {ticker} to run the demo.")

    price = _safe_float(closes.iloc[-1])
    sma20 = _safe_float(closes.tail(20).mean())
    sma50 = _safe_float(closes.tail(50).mean()) if len(closes) >= 50 else _safe_float(closes.mean())
    rsi = _rsi(closes)
    month_ago = _safe_float(closes.iloc[-22]) if len(closes) >= 22 else _safe_float(closes.iloc[0])
    change_1m = None
    if price is not None and month_ago not in (None, 0):
        change_1m = ((price - month_ago) / month_ago) * 100

    pe = _safe_float(info.get("trailingPE") or info.get("forwardPE"))
    revenue_growth = _safe_float(info.get("revenueGrowth"))
    if revenue_growth is not None and abs(revenue_growth) < 5:
        revenue_growth *= 100
    profit_margin = _safe_float(info.get("profitMargins"))
    if profit_margin is not None and abs(profit_margin) <= 1:
        profit_margin *= 100
    name = (
        info.get("longName")
        or info.get("shortName")
        or info.get("displayName")
        or ticker
    )

    score = 50
    technical_points: list[str] = []
    fundamental_points: list[str] = []
    risks: list[str] = []

    # —— Technical scoring ——
    if sma20 is not None and sma50 is not None and price is not None:
        if price > sma20 > sma50:
            score += 14
            technical_points.append(
                f"Price (${price:,.2f}) sits above the 20-day and 50-day averages — bullish trend structure."
            )
        elif price > sma50:
            score += 6
            technical_points.append(
                f"Price holds above the 50-day average (${sma50:,.2f}), a constructive longer-term signal."
            )
        elif price < sma20 < sma50:
            score -= 12
            technical_points.append(
                f"Price trades below both key averages — near-term trend looks weak."
            )
        else:
            score -= 3
            technical_points.append("Trend is mixed versus the 20-day and 50-day moving averages.")

    if rsi is not None:
        if 45 <= rsi <= 65:
            score += 8
            technical_points.append(f"RSI at {rsi:.0f} suggests healthy momentum without extreme overbought pressure.")
        elif rsi > 70:
            score -= 8
            technical_points.append(f"RSI at {rsi:.0f} is elevated — pullback risk is higher in the short term.")
            risks.append("Momentum looks stretched on RSI; entries may favor waiting for cooler conditions.")
        elif rsi < 35:
            score += 4
            technical_points.append(f"RSI at {rsi:.0f} is subdued — potential mean-reversion setup, but confirm the trend.")
        else:
            technical_points.append(f"RSI at {rsi:.0f} is in a neutral band.")

    if change_1m is not None:
        if change_1m > 8:
            score += 5
            technical_points.append(f"One-month performance is strong at {change_1m:+.1f}%.")
        elif change_1m < -8:
            score -= 6
            technical_points.append(f"One-month performance is soft at {change_1m:+.1f}%.")

    # —— Fundamental scoring ——
    if revenue_growth is not None:
        if revenue_growth >= 12:
            score += 12
            fundamental_points.append(f"Revenue growth around {revenue_growth:.1f}% supports a growth narrative.")
        elif revenue_growth >= 3:
            score += 5
            fundamental_points.append(f"Revenue growth near {revenue_growth:.1f}% is steady.")
        elif revenue_growth < 0:
            score -= 8
            fundamental_points.append(f"Revenue growth is negative ({revenue_growth:.1f}%).")
            risks.append("Top-line contraction can pressure multiples if it persists.")
        else:
            fundamental_points.append(f"Revenue growth is modest at {revenue_growth:.1f}%.")

    if profit_margin is not None:
        if profit_margin >= 15:
            score += 8
            fundamental_points.append(f"Profit margin near {profit_margin:.1f}% indicates solid profitability.")
        elif profit_margin >= 5:
            score += 3
            fundamental_points.append(f"Profit margin around {profit_margin:.1f}% is serviceable.")
        elif profit_margin < 0:
            score -= 7
            fundamental_points.append("The company is currently unprofitable on net margins.")
            risks.append("Negative margins raise execution and funding risk.")

    if pe is not None:
        if pe > 45:
            score -= 7
            fundamental_points.append(f"Trailing/forward P/E near {pe:.1f} is rich versus typical market levels.")
            risks.append("Valuation sits above historical averages — upside may require continued outperformance.")
        elif pe > 28:
            score -= 2
            fundamental_points.append(f"P/E near {pe:.1f} is somewhat elevated.")
            risks.append("Valuation is slightly above a conservative historical band.")
        elif 8 <= pe <= 22:
            score += 6
            fundamental_points.append(f"P/E near {pe:.1f} looks reasonable on a relative basis.")
        elif pe > 0:
            fundamental_points.append(f"P/E near {pe:.1f} is part of the valuation picture.")

    if not technical_points:
        technical_points.append("Limited technical confirmation from available history.")
    if not fundamental_points:
        fundamental_points.append("Fundamentals were partially available; treat the read as directional.")
    if not risks:
        risks.append("All equities carry market and company-specific risk, including possible loss of principal.")

    score = max(8, min(92, score))
    if score >= 68:
        verdict = "Buy"
        technical_label = "Bullish trend"
    elif score >= 55:
        verdict = "Moderate Buy"
        technical_label = "Constructive trend"
    elif score >= 45:
        verdict = "Hold"
        technical_label = "Neutral / mixed"
    else:
        verdict = "Caution"
        technical_label = "Weak / pressured"

    if revenue_growth is not None and revenue_growth >= 10:
        fundamental_label = "Strong revenue growth"
    elif revenue_growth is not None and revenue_growth >= 0:
        fundamental_label = "Steady fundamentals"
    elif profit_margin is not None and profit_margin >= 15:
        fundamental_label = "High-quality margins"
    else:
        fundamental_label = "Mixed fundamentals"

    confidence = int(max(55, min(93, 50 + abs(score - 50) * 0.9 + (8 if pe and sma50 else 0))))

    return {
        "ticker": ticker,
        "company": str(name),
        "query": f"Should I buy {ticker}?",
        "recommendation": verdict,
        "confidence": confidence,
        "technical_label": technical_label,
        "technical_detail": technical_points[0],
        "fundamental_label": fundamental_label,
        "fundamental_detail": fundamental_points[0],
        "risk_label": risks[0].split("—")[0].split(".")[0].strip()[:72],
        "risk_detail": risks[0] if risks[0].endswith(".") else risks[0] + ".",
        "price": price,
        "disclaimer": "Live demo using market data. Educational only — not financial advice.",
    }
