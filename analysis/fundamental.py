"""Fundamental analysis metrics and explanations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import yfinance as yf

METRIC_EXPLANATIONS = {
    "Revenue growth": (
        "**Revenue growth** shows how fast a company's sales are increasing year over year. "
        "Positive growth means the business is bringing in more money; negative growth means sales are shrinking."
    ),
    "Earnings growth": (
        "**Earnings growth** tracks how fast profit (net income) is changing. Growing earnings can mean "
        "the company is becoming more profitable, though one-time events can distort the number."
    ),
    "Free cash flow": (
        "**Free cash flow (FCF)** is the cash left after running the business and paying for capital "
        "expenses. Positive FCF means the company generates cash it can use for debt, dividends, or reinvestment."
    ),
    "Debt": (
        "**Total debt** is what the company owes lenders. Higher debt can mean higher risk, especially if "
        "cash flow is weak. Context matters — some industries normally carry more debt than others."
    ),
    "Gross margin": (
        "**Gross margin** is revenue minus the direct cost of making products/services, expressed as a "
        "percentage of revenue. Higher gross margins often mean stronger pricing power or lower production costs."
    ),
    "Operating margin": (
        "**Operating margin** shows profit from core operations as a percentage of revenue, after operating "
        "expenses but before interest and taxes. It reflects how efficiently the business runs day to day."
    ),
    "Net margin": (
        "**Net margin** is the percentage of revenue that becomes profit after all expenses. It is a "
        "bottom-line measure of overall profitability."
    ),
    "ROE": (
        "**ROE (Return on Equity)** measures how much profit a company generates per dollar of shareholder "
        "equity. Higher ROE can mean efficient use of investor capital, but very high values can also reflect "
        "high leverage."
    ),
    "ROIC": (
        "**ROIC (Return on Invested Capital)** estimates how well a company turns all invested capital "
        "(debt + equity) into profit. It helps compare how efficiently different businesses use their resources."
    ),
    "P/E ratio": (
        "**P/E ratio** compares share price to earnings per share. A higher P/E can mean investors expect "
        "faster future growth; a lower P/E can mean slower growth expectations or a cheaper valuation."
    ),
    "Forward P/E": (
        "**Forward P/E** uses expected future earnings instead of past earnings. It reflects what investors "
        "are paying today for estimated profits ahead."
    ),
    "Price / Sales": (
        "**Price-to-Sales** compares market value to total revenue. It is useful when earnings are low or "
        "negative, because it values the company based on sales instead of profit."
    ),
    "Price / Book": (
        "**Price-to-Book** compares market value to accounting book value. Below 1 can mean the market values "
        "the company below its net assets on paper."
    ),
    "EV / EBITDA": (
        "**EV/EBITDA** compares total company value (including debt) to operating earnings before interest, "
        "taxes, and depreciation. It is a common way to compare valuations across companies."
    ),
}


@dataclass
class FundamentalMetrics:
    """Fundamental analysis snapshot."""

    revenue_growth: float | None
    earnings_growth: float | None
    free_cash_flow: float | None
    total_debt: float | None
    gross_margin: float | None
    operating_margin: float | None
    net_margin: float | None
    roe: float | None
    roic: float | None
    pe_ratio: float | None
    forward_pe: float | None
    price_to_sales: float | None
    price_to_book: float | None
    ev_to_ebitda: float | None


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


def _yoy_growth(series: pd.Series) -> float | None:
    clean = series.dropna()
    if len(clean) < 2:
        return None
    latest = float(clean.iloc[0])
    prior = float(clean.iloc[1])
    if prior == 0:
        return None
    return ((latest - prior) / abs(prior)) * 100


def _find_row(df: pd.DataFrame, labels: list[str]) -> pd.Series | None:
    for label in labels:
        if label in df.index:
            return df.loc[label]
    return None


def _margin(numerator: float | None, revenue: float | None) -> float | None:
    if numerator is None or revenue in (None, 0):
        return None
    return (numerator / revenue) * 100


def fetch_fundamental_metrics(ticker: str) -> FundamentalMetrics:
    """Fetch and compute fundamental metrics for a ticker."""
    symbol = ticker.upper().strip()
    stock = yf.Ticker(symbol)
    info = stock.info or {}

    financials = stock.financials
    cashflow = stock.cashflow
    balance = stock.balance_sheet

    revenue_series = _find_row(financials, ["Total Revenue", "Revenue"])
    net_income_series = _find_row(financials, ["Net Income", "Net Income Common Stockholders"])

    revenue_growth = _yoy_growth(revenue_series) if revenue_series is not None else None
    earnings_growth = _yoy_growth(net_income_series) if net_income_series is not None else None

    fcf_series = _find_row(
        cashflow,
        ["Free Cash Flow", "FreeCashFlow"],
    )
    free_cash_flow = _safe_float(fcf_series.iloc[0]) if fcf_series is not None and len(fcf_series) else None

    debt_series = _find_row(
        balance,
        ["Total Debt", "Long Term Debt And Capital Lease Obligation", "Long Term Debt"],
    )
    total_debt = _safe_float(debt_series.iloc[0]) if debt_series is not None and len(debt_series) else None
    if total_debt is None:
        total_debt = _safe_float(info.get("totalDebt"))

    latest_revenue = _safe_float(revenue_series.iloc[0]) if revenue_series is not None and len(revenue_series) else None

    gross_profit_row = _find_row(financials, ["Gross Profit"])
    operating_income_row = _find_row(financials, ["Operating Income", "EBIT"])

    gross_profit = (
        _safe_float(gross_profit_row.iloc[0])
        if gross_profit_row is not None and len(gross_profit_row)
        else None
    )
    operating_income = (
        _safe_float(operating_income_row.iloc[0])
        if operating_income_row is not None and len(operating_income_row)
        else None
    )
    net_income = (
        _safe_float(net_income_series.iloc[0])
        if net_income_series is not None and len(net_income_series)
        else None
    )

    gross_margin = _margin(gross_profit, latest_revenue)
    operating_margin = _margin(operating_income, latest_revenue)
    net_margin = _margin(net_income, latest_revenue)

    roe = _safe_float(info.get("returnOnEquity"))
    if roe is not None and abs(roe) < 1:
        roe *= 100

    roic = _safe_float(info.get("returnOnCapitalEmployed") or info.get("returnOnAssets"))
    if roic is not None and abs(roic) < 1:
        roic *= 100

    return FundamentalMetrics(
        revenue_growth=revenue_growth,
        earnings_growth=earnings_growth,
        free_cash_flow=free_cash_flow,
        total_debt=total_debt,
        gross_margin=gross_margin,
        operating_margin=operating_margin,
        net_margin=net_margin,
        roe=roe,
        roic=roic,
        pe_ratio=_safe_float(info.get("trailingPE")),
        forward_pe=_safe_float(info.get("forwardPE")),
        price_to_sales=_safe_float(info.get("priceToSalesTrailing12Months")),
        price_to_book=_safe_float(info.get("priceToBook")),
        ev_to_ebitda=_safe_float(info.get("enterpriseToEbitda")),
    )
