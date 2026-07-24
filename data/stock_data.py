"""Stock data fetching via yfinance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import yfinance as yf


@dataclass
class StockQuote:
    """Snapshot of key stock metrics."""

    ticker: str
    company_name: str
    current_price: float | None
    daily_change: float | None
    daily_change_pct: float | None
    market_cap: int | None
    fifty_two_week_high: float | None
    fifty_two_week_low: float | None
    pe_ratio: float | None
    dividend_yield: float | None


class StockLookupError(Exception):
    """Raised when a ticker cannot be resolved."""


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return result


def _safe_int(value: Any) -> int | None:
    number = _safe_float(value)
    if number is None:
        return None
    return int(number)


def _resolve_dividend_yield(info: dict[str, Any]) -> float | None:
    """Return dividend yield as a percentage, if available."""
    for key in ("dividendYield", "trailingAnnualDividendYield", "yield"):
        raw = info.get(key)
        value = _safe_float(raw)
        if value is None:
            continue
        # yfinance may return 0.0053 for 0.53% or 0.53 for 0.53%.
        return value * 100 if value < 1 else value
    return None


def _resolve_pe_ratio(info: dict[str, Any]) -> float | None:
    for key in ("trailingPE", "forwardPE"):
        value = _safe_float(info.get(key))
        if value is not None:
            return value
    return None


def _resolve_company_name(info: dict[str, Any], ticker: str) -> str:
    for key in ("longName", "shortName", "displayName"):
        name = info.get(key)
        if isinstance(name, str) and name.strip():
            return name.strip()
    return ticker


def fetch_stock_quote(ticker: str) -> StockQuote:
    """Fetch current quote and fundamentals for a ticker."""
    symbol = ticker.upper().strip()
    if not symbol:
        raise StockLookupError("Enter a ticker symbol to search.")

    stock = yf.Ticker(symbol)
    info = stock.info or {}

    if not info or (info.get("regularMarketPrice") is None and info.get("currentPrice") is None):
        history = stock.history(period="5d")
        if history.empty:
            raise StockLookupError(f"No data found for ticker '{symbol}'.")

    current_price = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
    daily_change = _safe_float(info.get("regularMarketChange"))
    daily_change_pct = _safe_float(info.get("regularMarketChangePercent"))

    if daily_change is None or daily_change_pct is None:
        history = stock.history(period="5d")
        if len(history) >= 2:
            prior_close = float(history["Close"].iloc[-2])
            latest_close = float(history["Close"].iloc[-1])
            if current_price is None:
                current_price = latest_close
            if daily_change is None and current_price is not None:
                daily_change = current_price - prior_close
            if daily_change_pct is None and prior_close:
                daily_change_pct = (daily_change / prior_close) * 100 if daily_change else None

    return StockQuote(
        ticker=symbol,
        company_name=_resolve_company_name(info, symbol),
        current_price=current_price,
        daily_change=daily_change,
        daily_change_pct=daily_change_pct,
        market_cap=_safe_int(info.get("marketCap")),
        fifty_two_week_high=_safe_float(info.get("fiftyTwoWeekHigh")),
        fifty_two_week_low=_safe_float(info.get("fiftyTwoWeekLow")),
        pe_ratio=_resolve_pe_ratio(info),
        dividend_yield=_resolve_dividend_yield(info),
    )


def fetch_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch historical OHLCV data for charting."""
    symbol = ticker.upper().strip()
    stock = yf.Ticker(symbol)
    history = stock.history(period=period, auto_adjust=True)

    if history.empty:
        raise StockLookupError(f"No price history found for ticker '{symbol}'.")

    return history


def format_currency(value: float | None, *, prefix: str = "$") -> str:
    if value is None:
        return "—"
    return f"{prefix}{value:,.2f}"


def format_large_number(value: int | None) -> str:
    if value is None:
        return "—"
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,}"


def format_percent(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "—"
    if signed and value > 0:
        return f"+{value:.2f}%"
    return f"{value:.2f}%"
