"""Watchlist quote enrichment and ticker resolution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import yfinance as yf

from data.common_stocks import get_commonly_traded
from data.stock_data import StockLookupError, _resolve_company_name, _safe_int, fetch_stock_quote


@dataclass
class WatchlistCardData:
    ticker: str
    company_name: str
    current_price: float | None
    daily_change_pct: float | None
    market_cap: int | None
    sector: str
    sparkline: list[float] = field(default_factory=list)


def resolve_symbol(query: str) -> str:
    """Resolve a ticker symbol or company name to a Yahoo Finance ticker."""
    raw = (query or "").strip()
    if not raw:
        raise ValueError("Enter a ticker or company name.")

    # Direct ticker-style input
    candidate = raw.upper().replace(" ", "")
    if re_is_ticker(candidate):
        try:
            fetch_stock_quote(candidate)
            return candidate
        except StockLookupError:
            pass

    lowered = raw.lower()
    for item in get_commonly_traded():
        if item["ticker"].lower() == lowered or item["name"].lower() == lowered:
            return item["ticker"]
        if lowered in item["name"].lower() or lowered in item["ticker"].lower():
            return item["ticker"]

    # Fallback: treat cleaned input as ticker
    if re_is_ticker(candidate):
        raise StockLookupError(f"No data found for '{raw}'.")

    raise ValueError(
        f"Could not resolve '{raw}'. Try a ticker like AAPL or a known company name."
    )


def re_is_ticker(value: str) -> bool:
    cleaned = value.upper().strip()
    if not cleaned or len(cleaned) > 6:
        return False
    return all(ch.isalnum() or ch in {".", "-"} for ch in cleaned)


def _sector_for(symbol: str, info: dict) -> str:
    sector = str(info.get("sector") or "Unknown").strip() or "Unknown"
    if sector != "Unknown":
        return sector
    for item in get_commonly_traded():
        if item["ticker"] == symbol:
            return item["sector"]
    return "Unknown"


def fetch_watchlist_card(ticker: str) -> WatchlistCardData:
    """Fetch quote, sector, and 30-day sparkline for a watchlist card."""
    symbol = ticker.upper().strip()
    quote = fetch_stock_quote(symbol)
    stock = yf.Ticker(symbol)
    info = stock.info or {}

    sparkline: list[float] = []
    try:
        history = stock.history(period="1mo", auto_adjust=True)
        if not history.empty and "Close" in history:
            sparkline = [float(value) for value in history["Close"].dropna().tolist()[-30:]]
    except Exception:
        sparkline = []

    return WatchlistCardData(
        ticker=symbol,
        company_name=quote.company_name or _resolve_company_name(info, symbol),
        current_price=quote.current_price,
        daily_change_pct=quote.daily_change_pct,
        market_cap=quote.market_cap or _safe_int(info.get("marketCap")),
        sector=_sector_for(symbol, info),
        sparkline=sparkline,
    )


def _sparkline_from_download(data, ticker: str, multi_ticker: bool) -> list[float]:
    try:
        if multi_ticker:
            if ticker not in data.columns.get_level_values(0):
                return []
            closes = data[ticker]["Close"].dropna()
        else:
            closes = data["Close"].dropna()
        if closes.empty:
            return []
        return [float(value) for value in closes.tolist()[-30:]]
    except Exception:
        return []


def fetch_watchlist_cards(tickers: list[str]) -> list[WatchlistCardData]:
    """Fetch watchlist cards with batched history + parallel quote lookups."""
    symbols = [ticker.upper().strip() for ticker in tickers if ticker and str(ticker).strip()]
    if not symbols:
        return []

    spark_map: dict[str, list[float]] = {symbol: [] for symbol in symbols}
    try:
        history = yf.download(
            tickers=symbols,
            period="1mo",
            group_by="ticker",
            threads=True,
            progress=False,
            auto_adjust=True,
        )
        multi = getattr(history.columns, "nlevels", 1) > 1
        for symbol in symbols:
            spark_map[symbol] = _sparkline_from_download(history, symbol, multi)
    except Exception:
        pass

    cards_by_symbol: dict[str, WatchlistCardData] = {}

    def _load_one(symbol: str) -> WatchlistCardData:
        try:
            quote = fetch_stock_quote(symbol)
            info: dict = {}
            try:
                info = yf.Ticker(symbol).info or {}
            except Exception:
                info = {}
            return WatchlistCardData(
                ticker=symbol,
                company_name=quote.company_name or _resolve_company_name(info, symbol),
                current_price=quote.current_price,
                daily_change_pct=quote.daily_change_pct,
                market_cap=quote.market_cap or _safe_int(info.get("marketCap")),
                sector=_sector_for(symbol, info),
                sparkline=spark_map.get(symbol, []),
            )
        except Exception:
            return WatchlistCardData(
                ticker=symbol,
                company_name=symbol,
                current_price=None,
                daily_change_pct=None,
                market_cap=None,
                sector="Unknown",
                sparkline=spark_map.get(symbol, []),
            )

    workers = min(8, len(symbols))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_load_one, symbol): symbol for symbol in symbols}
        for future in as_completed(futures):
            card = future.result()
            cards_by_symbol[card.ticker] = card

    return [cards_by_symbol[symbol] for symbol in symbols if symbol in cards_by_symbol]
