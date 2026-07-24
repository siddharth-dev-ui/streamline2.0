"""Local persistence for portfolio holdings."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent
PORTFOLIO_PATH = DATA_DIR / "portfolio.json"


def _empty_portfolio() -> dict[str, Any]:
    return {"holdings": [], "updated_at": None}


def _normalize_holding(holding: dict[str, Any]) -> dict[str, Any]:
    ticker = str(holding.get("ticker", "")).upper().strip()
    shares = float(holding.get("shares", 0))
    avg_cost = float(holding.get("avg_cost", 0))
    if not ticker:
        raise ValueError("Ticker is required.")
    if shares <= 0:
        raise ValueError("Shares must be greater than zero.")
    if avg_cost <= 0:
        raise ValueError("Average cost must be greater than zero.")
    return {"ticker": ticker, "shares": shares, "avg_cost": avg_cost}


def load_holdings() -> list[dict[str, Any]]:
    """Load portfolio holdings from disk."""
    if not PORTFOLIO_PATH.exists():
        return []

    try:
        with PORTFOLIO_PATH.open(encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(data, dict):
        return []

    holdings = data.get("holdings") or []
    if not isinstance(holdings, list):
        return []

    normalized: list[dict[str, Any]] = []
    for holding in holdings:
        if not isinstance(holding, dict):
            continue
        try:
            normalized.append(_normalize_holding(holding))
        except (TypeError, ValueError):
            continue
    return normalized


def save_holdings(holdings: list[dict[str, Any]]) -> None:
    """Persist portfolio holdings to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "holdings": [_normalize_holding(holding) for holding in holdings],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with PORTFOLIO_PATH.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def add_holding(ticker: str, shares: float, avg_cost: float) -> None:
    """Add or update a holding in the portfolio."""
    holding = _normalize_holding({"ticker": ticker, "shares": shares, "avg_cost": avg_cost})
    holdings = load_holdings()
    updated = False
    for index, existing in enumerate(holdings):
        if existing["ticker"] == holding["ticker"]:
            holdings[index] = holding
            updated = True
            break
    if not updated:
        holdings.append(holding)
    save_holdings(holdings)


def remove_holding(ticker: str) -> None:
    """Remove a holding from the portfolio."""
    symbol = ticker.upper().strip()
    holdings = [item for item in load_holdings() if item["ticker"] != symbol]
    save_holdings(holdings)
