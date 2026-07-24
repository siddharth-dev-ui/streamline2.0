"""Portfolio analytics: allocation, sectors, returns, and risk."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import yfinance as yf

from data.stock_data import _resolve_company_name, _safe_float


@dataclass
class Position:
    ticker: str
    company_name: str
    shares: float
    avg_cost: float
    current_price: float
    market_value: float
    cost_basis: float
    return_amount: float
    return_pct: float
    weight: float
    sector: str
    beta: float | None


@dataclass
class PortfolioAnalytics:
    positions: list[Position]
    total_value: float
    total_cost: float
    total_return_amount: float
    total_return_pct: float
    allocation: dict[str, float] = field(default_factory=dict)
    sector_weights: dict[str, float] = field(default_factory=dict)
    risk_score: int = 0
    risk_reasoning: str = ""


def _annualized_volatility(ticker: str) -> float | None:
    history = yf.Ticker(ticker).history(period="1y", auto_adjust=True)
    if history.empty or len(history) < 20:
        return None
    returns = history["Close"].pct_change().dropna()
    if returns.empty:
        return None
    return float(returns.std() * np.sqrt(252))


def _build_position(holding: dict) -> Position:
    ticker = holding["ticker"]
    shares = float(holding["shares"])
    avg_cost = float(holding["avg_cost"])

    stock = yf.Ticker(ticker)
    info = stock.info or {}
    current_price = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
    if current_price is None:
        history = stock.history(period="5d", auto_adjust=True)
        if not history.empty:
            current_price = float(history["Close"].iloc[-1])
    if current_price is None:
        raise RuntimeError(f"Unable to fetch a current price for {ticker}.")

    cost_basis = shares * avg_cost
    market_value = shares * current_price
    return_amount = market_value - cost_basis
    return_pct = (return_amount / cost_basis) * 100 if cost_basis else 0.0
    sector = str(info.get("sector") or "Unknown").strip() or "Unknown"
    beta = _safe_float(info.get("beta"))

    return Position(
        ticker=ticker,
        company_name=_resolve_company_name(info, ticker),
        shares=shares,
        avg_cost=avg_cost,
        current_price=current_price,
        market_value=market_value,
        cost_basis=cost_basis,
        return_amount=return_amount,
        return_pct=return_pct,
        weight=0.0,
        sector=sector,
        beta=beta,
    )


def _compute_risk_score(positions: list[Position], sector_weights: dict[str, float]) -> tuple[int, str]:
    if not positions:
        return 0, "Add holdings to calculate portfolio risk."

    total_value = sum(position.market_value for position in positions)
    if total_value <= 0:
        return 0, "Portfolio value is zero, so risk cannot be estimated."

    max_weight = max(position.weight for position in positions)
    max_sector_weight = max(sector_weights.values()) if sector_weights else 0.0
    holding_count = len(positions)

    weighted_beta = 0.0
    beta_weight = 0.0
    weighted_vol = 0.0
    vol_weight = 0.0

    for position in positions:
        weight = position.market_value / total_value
        if position.beta is not None:
            weighted_beta += position.beta * weight
            beta_weight += weight
        volatility = _annualized_volatility(position.ticker)
        if volatility is not None:
            weighted_vol += volatility * weight
            vol_weight += weight

    portfolio_beta = weighted_beta / beta_weight if beta_weight else 1.0
    portfolio_vol = weighted_vol / vol_weight if vol_weight else 0.2

    score = 0
    reasons: list[str] = []

    if max_weight >= 50:
        score += 30
        reasons.append(
            f"Largest position is {max_weight:.0f}% of the portfolio, creating high single-stock concentration risk."
        )
    elif max_weight >= 35:
        score += 20
        reasons.append(
            f"Largest position is {max_weight:.0f}% of the portfolio, which is moderately concentrated."
        )
    elif max_weight >= 25:
        score += 12
        reasons.append(f"Top holding represents {max_weight:.0f}% of portfolio value.")

    if max_sector_weight >= 60:
        score += 25
        sector_name = max(sector_weights, key=sector_weights.get)
        reasons.append(
            f"{sector_name} accounts for {max_sector_weight:.0f}% of exposure, limiting sector diversification."
        )
    elif max_sector_weight >= 45:
        score += 15
        sector_name = max(sector_weights, key=sector_weights.get)
        reasons.append(f"{sector_name} is the dominant sector at {max_sector_weight:.0f}% of the portfolio.")

    if holding_count <= 2:
        score += 15
        reasons.append("Only a couple of holdings are held, so diversification across names is limited.")
    elif holding_count <= 4:
        score += 8
        reasons.append("A small number of holdings increases sensitivity to individual stock moves.")

    if portfolio_beta >= 1.35:
        score += 12
        reasons.append(f"Estimated portfolio beta is {portfolio_beta:.2f}, above the broad market.")
    elif portfolio_beta <= 0.75:
        score += 4
        reasons.append(f"Estimated portfolio beta is {portfolio_beta:.2f}, below the broad market.")

    if portfolio_vol >= 0.35:
        score += 18
        reasons.append(f"Annualized volatility is about {portfolio_vol * 100:.0f}%, which is elevated.")
    elif portfolio_vol >= 0.25:
        score += 10
        reasons.append(f"Annualized volatility is about {portfolio_vol * 100:.0f}%, above typical large-cap levels.")

    score = max(0, min(100, score))

    if not reasons:
        reasons.append(
            "Holdings are spread across multiple positions and sectors with moderate concentration and volatility."
        )

    label = "Low" if score < 35 else "Moderate" if score < 65 else "High"
    reasoning = f"Risk level: **{label}** ({score}/100). " + " ".join(reasons)
    return score, reasoning


def analyze_portfolio(holdings: list[dict]) -> PortfolioAnalytics:
    """Compute portfolio metrics from stored holdings."""
    if not holdings:
        raise ValueError("Add at least one holding to analyze your portfolio.")

    positions = [_build_position(holding) for holding in holdings]
    total_value = sum(position.market_value for position in positions)
    total_cost = sum(position.cost_basis for position in positions)
    total_return_amount = total_value - total_cost
    total_return_pct = (total_return_amount / total_cost) * 100 if total_cost else 0.0

    allocation: dict[str, float] = {}
    sector_totals: dict[str, float] = {}

    for position in positions:
        weight = (position.market_value / total_value) * 100 if total_value else 0.0
        position.weight = weight
        allocation[position.ticker] = weight
        sector_totals[position.sector] = sector_totals.get(position.sector, 0.0) + position.market_value

    sector_weights = {
        sector: (value / total_value) * 100 if total_value else 0.0
        for sector, value in sorted(sector_totals.items(), key=lambda item: item[1], reverse=True)
    }

    risk_score, risk_reasoning = _compute_risk_score(positions, sector_weights)

    return PortfolioAnalytics(
        positions=sorted(positions, key=lambda position: position.market_value, reverse=True),
        total_value=total_value,
        total_cost=total_cost,
        total_return_amount=total_return_amount,
        total_return_pct=total_return_pct,
        allocation=allocation,
        sector_weights=sector_weights,
        risk_score=risk_score,
        risk_reasoning=risk_reasoning,
    )
