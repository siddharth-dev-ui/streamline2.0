"""
StreamlineLLM — local custom investment language model.

Generates structured research, news, and portfolio analysis without any
external API. Combines market data scoring with natural-language templates
and investor-profile adaptation.
"""

from __future__ import annotations

import re
from typing import Any

from data.news_data import NEWS_CATEGORIES

POSITIVE_WORDS = {
    "beat",
    "beats",
    "surge",
    "surges",
    "rally",
    "rallies",
    "gain",
    "gains",
    "growth",
    "raise",
    "raises",
    "upgrade",
    "upgraded",
    "record",
    "profit",
    "profits",
    "strong",
    "outperform",
    "bullish",
    "expansion",
    "breakthrough",
    "approval",
    "soar",
    "soars",
    "jump",
    "jumps",
    "win",
    "wins",
}

NEGATIVE_WORDS = {
    "miss",
    "misses",
    "fall",
    "falls",
    "drop",
    "drops",
    "cut",
    "cuts",
    "downgrade",
    "downgraded",
    "lawsuit",
    "probe",
    "investigation",
    "weak",
    "slump",
    "slumps",
    "loss",
    "losses",
    "warn",
    "warning",
    "recall",
    "layoff",
    "layoffs",
    "bankruptcy",
    "fraud",
    "decline",
    "declines",
    "crash",
    "plunge",
    "selloff",
    "bearish",
}

HIGH_IMPACT_TERMS = {
    "federal reserve": 40,
    "fed ": 35,
    "interest rate": 35,
    "inflation": 30,
    "recession": 35,
    "tariff": 28,
    "war": 30,
    "geopolit": 28,
    "oil": 22,
    "opec": 24,
    "earnings": 20,
    "sec ": 18,
    "lawsuit": 18,
    "breakthrough": 20,
    "upgrade": 16,
    "downgrade": 16,
    "merger": 18,
    "acquisition": 18,
    "bankruptcy": 30,
    "stimulus": 22,
    "gdp": 20,
    "jobs report": 22,
    "cpi": 24,
    "treasury": 18,
}

CATEGORY_KEYWORDS = {
    "Earnings": ["earning", "eps", "revenue", "guidance", "quarter", "profit", "results"],
    "Analyst actions": ["upgrade", "downgrade", "price target", "analyst", "overweight", "underweight", "initiate"],
    "SEC filings": ["sec", "10-k", "10-q", "8-k", "filing", "form 4", "insider"],
    "Industry news": ["competitor", "industry", "chip", "ai ", "product", "launch", "partnership", "market share"],
    "Macroeconomic events": [
        "fed",
        "inflation",
        "rate",
        "recession",
        "gdp",
        "tariff",
        "oil",
        "war",
        "treasury",
        "jobs",
        "cpi",
    ],
}


def _safe(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _text_blob(*parts: Any) -> str:
    return " ".join(str(part or "") for part in parts).lower()


def score_headline_sentiment(text: str) -> int:
    """Score a headline from -100 to 100 using lexical polarity."""
    words = set(re.findall(r"[a-z0-9']+", text.lower()))
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    raw = (pos - neg) * 18
    return max(-100, min(100, raw))


def score_impact(text: str, portfolio_tickers: list[str] | None = None) -> int:
    """Higher is more market-moving."""
    lowered = text.lower()
    score = 5
    for term, weight in HIGH_IMPACT_TERMS.items():
        if term in lowered:
            score += weight
    if portfolio_tickers:
        for ticker in portfolio_tickers:
            if ticker.lower() in lowered:
                score += 25
    return score


def categorize_headline(title: str, summary: str = "") -> str:
    blob = _text_blob(title, summary)
    best = "Industry news"
    best_hits = 0
    for category, keywords in CATEGORY_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword in blob)
        if hits > best_hits:
            best_hits = hits
            best = category
    return best


def _beginner(profile: dict[str, Any]) -> bool:
    return (profile.get("experience") or "").lower() == "beginner"


def _conservative(profile: dict[str, Any]) -> bool:
    risk = (profile.get("risk_tolerance") or "").lower()
    return risk in {"very conservative", "conservative"}


def _aggressive(profile: dict[str, Any]) -> bool:
    risk = (profile.get("risk_tolerance") or "").lower()
    return risk in {"growth", "aggressive"}


class StreamlineLLM:
    """Custom local investment LLM."""

    name = "StreamlineLLM-Local"
    version = "1.0"

    def complete_json(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Route a structured generation task."""
        if task == "research":
            return self.research(context)
        if task == "stock_news":
            return self.analyze_stock_news(context)
        if task == "latest_news":
            return self.curate_latest_news(context)
        if task == "portfolio":
            return self.portfolio_advice(context)
        raise ValueError(f"Unknown StreamlineLLM task: {task}")

    def research(self, context: dict[str, Any]) -> dict[str, Any]:
        profile = context.get("user_profile") or {}
        quote = context.get("quote")
        technical = context.get("technical")
        fundamentals = context.get("fundamentals")
        news_summary = context.get("news_summary") or ""
        ticker = context.get("ticker")

        tech_score, tech_notes = self._score_technicals(technical)
        fund_score, fund_notes = self._score_fundamentals(fundamentals)
        news_score, news_notes = self._score_news_blob(news_summary)

        blended = 0.4 * tech_score + 0.45 * fund_score + 0.15 * news_score
        recommendation, confidence = self._recommendation_from_score(blended, profile)

        company = quote.company_name if quote else (ticker or "this opportunity")
        symbol = ticker or "N/A"
        price = getattr(quote, "current_price", None)

        if _beginner(profile):
            technical_reasoning = (
                f"Technicals for {symbol} currently score about {tech_score:.0f}/100. "
                + " ".join(tech_notes[:3])
                + " In plain terms: this looks at momentum and trend, not company quality."
            )
            fundamental_reasoning = (
                f"Fundamentals score about {fund_score:.0f}/100. "
                + " ".join(fund_notes[:3])
                + " Fundamentals ask whether the business is healthy and reasonably valued."
            )
        else:
            technical_reasoning = (
                f"Technical composite {tech_score:.0f}/100. " + " ".join(tech_notes)
            )
            fundamental_reasoning = (
                f"Fundamental composite {fund_score:.0f}/100. " + " ".join(fund_notes)
            )

        horizon = profile.get("investment_horizon") or "3–10 years"
        goal = profile.get("investment_goal") or "General investing"
        risk = profile.get("risk_tolerance") or "Moderate"

        profile_fit = self._profile_fit(
            recommendation=recommendation,
            profile=profile,
            tech_score=tech_score,
            fund_score=fund_score,
            company=company,
        )

        price_note = f" near ${price:,.2f}" if isinstance(price, (int, float)) else ""
        summary = (
            f"{recommendation} on {company} ({symbol}){price_note} with confidence {confidence}/100. "
            f"The blend of technical ({tech_score:.0f}), fundamental ({fund_score:.0f}), "
            f"and news ({news_score:.0f}) signals favors this stance for a {risk.lower()} investor "
            f"focused on {goal.lower()}."
        )

        risks = self._research_risks(profile, tech_score, fund_score, news_score)
        uncertainties = [
            "This local model uses rules and templates, not live proprietary analyst forecasts.",
            "Forward guidance, segment mix, and sudden news can change the thesis quickly.",
        ]
        if not technical:
            uncertainties.append("Technical indicators were incomplete for this ticker.")
        if not fundamentals:
            uncertainties.append("Fundamental metrics were incomplete for this ticker.")

        return {
            "primary_ticker": ticker,
            "recommendation": recommendation,
            "confidence_score": confidence,
            "technical_reasoning": technical_reasoning,
            "fundamental_reasoning": fundamental_reasoning,
            "news_impact": news_notes,
            "risks": risks,
            "investment_horizon": (
                f"Aligned to your stated horizon of {horizon}. "
                f"For this thesis, a review window of several months to a few years is appropriate "
                f"depending on how the business executes."
            ),
            "important_uncertainties": uncertainties,
            "profile_fit": profile_fit,
            "summary": summary,
        }

    def analyze_stock_news(self, context: dict[str, Any]) -> dict[str, Any]:
        headlines = context.get("headlines") or []
        company = context.get("company_name") or context.get("ticker") or "This stock"
        ticker = context.get("ticker") or ""

        categories = {name: [] for name in NEWS_CATEGORIES}
        scores: list[int] = []

        for item in headlines:
            title = item.get("title") or ""
            summary = item.get("summary") or title
            publisher = item.get("publisher") or "Unknown"
            score = score_headline_sentiment(_text_blob(title, summary))
            scores.append(score)
            category = categorize_headline(title, summary)
            tone = "constructive" if score > 15 else "cautious" if score < -15 else "mixed"
            categories[category].append(
                {
                    "title": title,
                    "summary": (
                        f"{summary[:180] if summary else title} "
                        f"Local read: tone looks {tone} for {ticker or company}."
                    ).strip(),
                    "source": publisher,
                }
            )

        avg = int(round(sum(scores) / len(scores))) if scores else 0
        avg = max(-100, min(100, avg))

        positives = [h["title"] for h, s in zip(headlines, scores) if s > 15][:2]
        negatives = [h["title"] for h, s in zip(headlines, scores) if s < -15][:2]

        reasoning_parts = [f"Average lexical sentiment across {len(headlines)} headlines is {avg:+d}."]
        if positives:
            reasoning_parts.append("Supportive headlines include: " + "; ".join(positives) + ".")
        if negatives:
            reasoning_parts.append("More cautious headlines include: " + "; ".join(negatives) + ".")
        if not positives and not negatives:
            reasoning_parts.append("Most headlines look relatively neutral on wording alone.")

        populated = [name for name, items in categories.items() if items]
        summary = (
            f"Recent coverage for {company} ({ticker}) spans {len(headlines)} headlines. "
            f"Overall sentiment scores {avg:+d}. "
            f"Most relevant themes: {', '.join(populated) if populated else 'general market chatter'}."
        )

        return {
            "summary": summary,
            "sentiment_score": avg,
            "sentiment_reasoning": " ".join(reasoning_parts),
            "categories": categories,
        }

    def curate_latest_news(self, context: dict[str, Any]) -> dict[str, Any]:
        pool = context.get("articles") or []
        portfolio_tickers = context.get("portfolio_tickers") or []

        ranked = sorted(
            pool,
            key=lambda article: score_impact(
                _text_blob(article.get("title"), article.get("summary")),
                portfolio_tickers,
            ),
            reverse=True,
        )

        stories = []
        for article in ranked[:8]:
            title = article.get("title") or ""
            summary = article.get("summary") or title
            impact_score = score_impact(_text_blob(title, summary), portfolio_tickers)
            related = []
            if article.get("related_ticker"):
                related.append(str(article["related_ticker"]).upper())
            for ticker in portfolio_tickers:
                if ticker.lower() in title.lower() and ticker not in related:
                    related.append(ticker)

            why = (
                f"This ranks high on macro/market-impact keywords"
                + (f" and touches portfolio name(s) {', '.join(related)}" if related else "")
                + ". Watch for spillover into risk appetite and sector leadership."
            )
            stories.append(
                {
                    "title": title,
                    "summary": (summary[:220] if summary else title),
                    "impact": "High" if impact_score >= 40 else "Medium",
                    "why_it_matters": why,
                    "related_tickers": related,
                    "source": article.get("publisher") or article.get("source_label") or "News",
                    "url": article.get("url") or "",
                    "image": article.get("image") or "",
                    "published": article.get("published") or "",
                }
            )

        if portfolio_tickers:
            briefing = (
                f"StreamlineLLM scanned world/business feeds plus news tied to "
                f"{', '.join(portfolio_tickers)}. The highest-impact items center on "
                f"macro policy, geopolitics, and names linked to your book."
            )
        else:
            briefing = (
                "StreamlineLLM scanned world and business headlines. "
                "The top items emphasize macro policy, geopolitics, and market-moving sector news. "
                "Add portfolio holdings to personalize this briefing further."
            )

        return {"briefing": briefing, "stories": stories}

    def portfolio_advice(self, context: dict[str, Any]) -> dict[str, Any]:
        analytics = context["analytics"]
        profile = context.get("profile") or {}

        suggestions: list[dict[str, str]] = []
        positions = analytics.positions
        sector_weights = analytics.sector_weights
        max_weight = max((p.weight for p in positions), default=0.0)
        top = positions[0] if positions else None
        top_sector = next(iter(sector_weights.items()), (None, 0.0))

        if top and max_weight >= 35:
            suggestions.append(
                {
                    "title": f"Reduce single-name concentration in {top.ticker}",
                    "rationale": (
                        f"{top.ticker} is about {top.weight:.0f}% of the portfolio. "
                        "That amplifies idiosyncratic risk. Trimming toward a lower weight "
                        "or pairing it with uncorrelated exposures can stabilize returns."
                    ),
                }
            )

        if top_sector[0] and top_sector[1] >= 45:
            suggestions.append(
                {
                    "title": f"Broaden beyond {top_sector[0]}",
                    "rationale": (
                        f"{top_sector[0]} is roughly {top_sector[1]:.0f}% of exposure. "
                        "Adding quality names or ETFs from underweight sectors can reduce "
                        "sector drawdowns when leadership rotates."
                    ),
                }
            )

        if len(positions) <= 3:
            suggestions.append(
                {
                    "title": "Increase the number of independent holdings",
                    "rationale": (
                        f"Only {len(positions)} position(s) are held. "
                        "A small roster means each name dominates outcomes. "
                        "Adding a few complementary holdings can smooth volatility."
                    ),
                }
            )

        if _conservative(profile):
            suggestions.append(
                {
                    "title": "Prioritize defensive cash-flow quality",
                    "rationale": (
                        "Your profile leans conservative. Emphasizing durable free cash flow, "
                        "dividends, and lower-beta exposures (or broad ETFs) better matches "
                        "capital-preservation preferences."
                    ),
                }
            )
        elif _aggressive(profile):
            suggestions.append(
                {
                    "title": "Keep growth exposure deliberate, not accidental",
                    "rationale": (
                        "Your risk tolerance can support growth leadership, but concentration "
                        "still matters. Size speculative winners intentionally and balance with "
                        "core compounders so one unwind does not dominate the book."
                    ),
                }
            )
        else:
            suggestions.append(
                {
                    "title": "Rebalance growth vs stability",
                    "rationale": (
                        "A moderate profile usually benefits from a barbell: durable cash generators "
                        "plus selective growth. Rebalancing toward that mix can keep risk aligned "
                        "with your horizon."
                    ),
                }
            )

        if profile.get("interest_in_etfs"):
            suggestions.append(
                {
                    "title": "Use ETFs to fill factor or sector gaps",
                    "rationale": (
                        "You indicated interest in ETFs. A broad market or sector ETF can "
                        "efficiently cover holes without researching many individual names."
                    ),
                }
            )

        if profile.get("interest_in_dividends"):
            suggestions.append(
                {
                    "title": "Check income durability across holdings",
                    "rationale": (
                        "Dividend interest suggests reviewing payout quality and concentration. "
                        "Spreading income across sectors can reduce cutoff risk if one payer "
                        "cuts its distribution."
                    ),
                }
            )

        # Cap at 5 unique-ish suggestions
        trimmed = suggestions[:5]
        summary = (
            f"Portfolio risk score is {analytics.risk_score}/100 with "
            f"{len(positions)} holdings and total return {analytics.total_return_pct:+.1f}%. "
            "Suggestions below target concentration, sector balance, and alignment with your profile."
        )
        return {"summary": summary, "suggestions": trimmed}

    def _score_technicals(self, technical: Any) -> tuple[float, list[str]]:
        if not technical:
            return 50.0, ["Technical data was limited, so momentum is treated as neutral."]

        score = 50.0
        notes: list[str] = []
        rsi = _safe(getattr(technical, "rsi", None), 50.0)
        macd = _safe(getattr(technical, "macd", None))
        macd_signal = _safe(getattr(technical, "macd_signal", None))
        sma_50 = _safe(getattr(technical, "sma_50", None))
        sma_200 = _safe(getattr(technical, "sma_200", None))
        ema_20 = _safe(getattr(technical, "ema_20", None))

        if rsi >= 70:
            score -= 12
            notes.append(f"RSI at {rsi:.1f} signals overbought conditions.")
        elif rsi <= 30:
            score += 10
            notes.append(f"RSI at {rsi:.1f} signals oversold / potential mean-reversion setup.")
        else:
            notes.append(f"RSI at {rsi:.1f} is in a neutral zone.")

        if macd > macd_signal:
            score += 10
            notes.append("MACD is above its signal line (bullish momentum).")
        else:
            score -= 8
            notes.append("MACD is below its signal line (weaker momentum).")

        if sma_50 and sma_200:
            if sma_50 > sma_200:
                score += 12
                notes.append("SMA 50 is above SMA 200 (uptrend structure).")
            else:
                score -= 12
                notes.append("SMA 50 is below SMA 200 (downtrend structure).")

        if ema_20 and sma_50:
            if ema_20 >= sma_50:
                score += 6
                notes.append("EMA 20 is holding at or above the 50-day average.")
            else:
                score -= 6
                notes.append("EMA 20 is below the 50-day average.")

        return max(0.0, min(100.0, score)), notes

    def _score_fundamentals(self, fundamentals: Any) -> tuple[float, list[str]]:
        if not fundamentals:
            return 50.0, ["Fundamental data was limited, so quality/valuation is treated as neutral."]

        score = 50.0
        notes: list[str] = []

        revenue_growth = _safe(getattr(fundamentals, "revenue_growth", None))
        earnings_growth = _safe(getattr(fundamentals, "earnings_growth", None))
        roe = _safe(getattr(fundamentals, "roe", None))
        roic = _safe(getattr(fundamentals, "roic", None))
        net_margin = _safe(getattr(fundamentals, "net_margin", None))
        pe = _safe(getattr(fundamentals, "pe_ratio", None))
        fcf = _safe(getattr(fundamentals, "free_cash_flow", None))
        debt = _safe(getattr(fundamentals, "total_debt", None))

        if revenue_growth:
            if revenue_growth > 10:
                score += 10
                notes.append(f"Revenue growth around {revenue_growth:.1f}% supports expansion.")
            elif revenue_growth < 0:
                score -= 10
                notes.append(f"Revenue growth around {revenue_growth:.1f}% is a headwind.")
            else:
                notes.append(f"Revenue growth around {revenue_growth:.1f}% is modest.")

        if earnings_growth:
            if earnings_growth > 10:
                score += 8
                notes.append(f"Earnings growth near {earnings_growth:.1f}% is constructive.")
            elif earnings_growth < 0:
                score -= 8
                notes.append(f"Earnings growth near {earnings_growth:.1f}% is soft.")

        if roe:
            if roe >= 15:
                score += 8
                notes.append(f"ROE near {roe:.1f}% indicates solid capital returns.")
            elif roe < 5:
                score -= 6
                notes.append(f"ROE near {roe:.1f}% is relatively weak.")

        if roic:
            if roic >= 10:
                score += 6
                notes.append(f"ROIC near {roic:.1f}% looks healthy.")
            elif roic < 5:
                score -= 5
                notes.append(f"ROIC near {roic:.1f}% is underwhelming.")

        if net_margin:
            if net_margin >= 15:
                score += 6
                notes.append(f"Net margin near {net_margin:.1f}% shows strong profitability.")
            elif net_margin < 5:
                score -= 5
                notes.append(f"Net margin near {net_margin:.1f}% leaves less cushion.")

        if pe:
            if pe > 45:
                score -= 8
                notes.append(f"Trailing P/E near {pe:.1f} is elevated versus many large caps.")
            elif 0 < pe < 15:
                score += 6
                notes.append(f"Trailing P/E near {pe:.1f} looks comparatively inexpensive.")
            else:
                notes.append(f"Trailing P/E near {pe:.1f} is in a middle valuation band.")

        if fcf > 0:
            score += 5
            notes.append("Free cash flow is positive.")
        elif fcf < 0:
            score -= 6
            notes.append("Free cash flow is negative.")

        if debt > 0 and fcf > 0 and debt > 8 * fcf:
            score -= 5
            notes.append("Debt looks elevated versus free cash flow.")

        if not notes:
            notes.append("Core fundamentals are mixed without a clear extreme.")

        return max(0.0, min(100.0, score)), notes

    def _score_news_blob(self, news_summary: str) -> tuple[float, str]:
        if not news_summary or "No recent" in news_summary or "No ticker" in news_summary:
            return 50.0, "No rich company headline set was available; news impact is treated as neutral."

        score = score_headline_sentiment(news_summary)
        normalized = 50 + score / 2
        if score >= 25:
            note = "Recent headlines lean constructive and may support risk appetite in the name."
        elif score <= -25:
            note = "Recent headlines lean cautious and may weigh on near-term sentiment."
        else:
            note = "Recent headlines look mixed; news is unlikely to dominate the thesis alone."
        return max(0.0, min(100.0, normalized)), note

    def _recommendation_from_score(
        self, blended: float, profile: dict[str, Any]
    ) -> tuple[str, int]:
        adjusted = blended
        if _conservative(profile):
            adjusted -= 8
        elif _aggressive(profile):
            adjusted += 5

        if adjusted >= 78:
            rec = "Strong Buy"
        elif adjusted >= 64:
            rec = "Buy"
        elif adjusted >= 48:
            rec = "Hold"
        elif adjusted >= 36:
            rec = "Watchlist"
        elif adjusted >= 24:
            rec = "Sell"
        else:
            rec = "Strong Sell"

        confidence = int(max(35, min(92, 40 + abs(adjusted - 50) * 0.9)))
        return rec, confidence

    def _profile_fit(
        self,
        *,
        recommendation: str,
        profile: dict[str, Any],
        tech_score: float,
        fund_score: float,
        company: str,
    ) -> str:
        risk = profile.get("risk_tolerance") or "Moderate"
        goal = profile.get("investment_goal") or "General investing"
        horizon = profile.get("investment_horizon") or "3–10 years"
        experience = profile.get("experience") or "Beginner"

        parts = [
            f"This {recommendation} stance is framed for a {risk} investor pursuing {goal} "
            f"over a {horizon} horizon."
        ]

        if _conservative(profile):
            parts.append(
                f"Because you prioritize stability, the model put more weight on durable fundamentals "
                f"(score {fund_score:.0f}) and was more cautious about momentum-only strength "
                f"(technical score {tech_score:.0f})."
            )
        elif _aggressive(profile):
            parts.append(
                f"Given higher risk tolerance, growth/momentum evidence "
                f"(technical {tech_score:.0f}, fundamental {fund_score:.0f}) can support a more "
                f"constructive view on {company} when the blended score is elevated."
            )
        else:
            parts.append(
                f"For a balanced profile, both trend ({tech_score:.0f}) and business quality "
                f"({fund_score:.0f}) need to agree before conviction rises."
            )

        if experience == "Beginner":
            parts.append(
                "Explanations stay plain-language so the recommendation is easier to interpret "
                "without assuming advanced market jargon."
            )
        elif experience == "Advanced":
            parts.append(
                "Detail stays denser on metrics so you can stress-test the signal quickly."
            )

        if profile.get("interest_in_dividends") and recommendation in {"Buy", "Strong Buy", "Hold"}:
            parts.append("Dividend preference is noted: favor cash-return durability when sizing any position.")
        if profile.get("interest_in_etfs") and recommendation in {"Sell", "Strong Sell", "Watchlist"}:
            parts.append(
                "If single-stock risk feels high for your profile, a diversified ETF may be a cleaner vehicle "
                "than forcing a fit."
            )

        return " ".join(parts)

    def _research_risks(
        self,
        profile: dict[str, Any],
        tech_score: float,
        fund_score: float,
        news_score: float,
    ) -> list[str]:
        risks = [
            "Market regime shifts (rates, inflation, liquidity) can override single-stock signals.",
            "Data gaps or stale prints can distort both technical and fundamental readings.",
        ]
        if tech_score >= 70:
            risks.append("Extended momentum can reverse quickly if buyers step aside.")
        if tech_score <= 35:
            risks.append("Weak trend can persist longer than valuation investors expect.")
        if fund_score <= 40:
            risks.append("Soft fundamentals raise the chance that weakness is structural, not temporary.")
        if news_score <= 40:
            risks.append("Negative headline flow can extend multiple compression or sell pressure.")
        if _conservative(profile):
            risks.append("For a conservative profile, volatility around uncertain catalysts is especially costly.")
        return risks[:5]


# Singleton used across the app.
llm = StreamlineLLM()
