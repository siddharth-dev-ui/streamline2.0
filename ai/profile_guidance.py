"""Profile-aware research guidance for personalized recommendations."""

from __future__ import annotations

from typing import Any


def build_adaptation_guidance(profile: dict[str, Any]) -> str:
    """Translate the investor profile into explicit AI adaptation instructions."""
    risk = profile.get("risk_tolerance") or "Moderate"
    experience = profile.get("experience") or "Beginner"
    goal = profile.get("investment_goal") or "General investing"
    horizon = profile.get("investment_horizon") or "3–10 years"
    sectors = profile.get("preferred_sectors") or []
    etfs = profile.get("interest_in_etfs")
    dividends = profile.get("interest_in_dividends")

    lines: list[str] = [
        "Adapt this research to the investor below. Do not give a generic answer.",
        "",
        "Risk posture:",
    ]

    if risk in ("Very Conservative", "Conservative"):
        lines.append(
            "- Emphasize capital preservation, dividends, balance-sheet strength, "
            "lower volatility, and downside protection. Be cautious about speculative growth stories."
        )
    elif risk in ("Growth", "Aggressive"):
        lines.append(
            "- Emphasize growth potential, innovation, competitive advantage, and upside catalysts. "
            "Accept higher volatility when the thesis is strong, but still disclose risks clearly."
        )
    else:
        lines.append(
            "- Balance growth and stability. Weigh both upside potential and downside protection."
        )

    lines.extend(["", "Experience level:"])
    if experience == "Beginner":
        lines.append(
            "- Use plain language and short educational asides that explain what metrics mean. "
            "Avoid jargon unless you define it. Keep the structure easy to follow."
        )
    elif experience == "Advanced":
        lines.append(
            "- Use detailed metrics and concise analysis. Skip introductory definitions. "
            "Assume familiarity with valuation multiples, technical indicators, and risk concepts."
        )
    else:
        lines.append(
            "- Use clear language with moderate detail. Explain less-common metrics briefly, "
            "but do not oversimplify core analysis."
        )

    lines.extend(["", "Goals and preferences:"])
    goal_notes = {
        "Retirement": "Prioritize sustainability of returns and drawdown risk over speculative upside.",
        "Long-term growth": "Prioritize durable growth, reinvestment quality, and multi-year compounding.",
        "Passive income": "Prioritize dividend quality, payout sustainability, and cash-flow stability.",
        "Saving for a purchase": "Prioritize liquidity needs and capital preservation relative to the time horizon.",
        "General investing": "Keep the recommendation flexible and balanced across growth and stability.",
    }
    lines.append(f"- Goal ({goal}): {goal_notes.get(goal, 'Align the recommendation with the stated goal.')}")
    lines.append(f"- Stated horizon: {horizon}. Align investment_horizon with this unless the stock thesis clearly conflicts, and explain any mismatch.")

    if dividends:
        lines.append("- The investor is interested in dividends — highlight yield quality and payout sustainability when relevant.")
    if etfs:
        lines.append("- The investor is open to ETFs — mention diversified alternatives when single-stock risk looks high for their profile.")
    if sectors:
        lines.append(f"- Preferred sectors: {', '.join(sectors)}. Note alignment or conflict with these preferences.")

    lines.extend(
        [
            "",
            "Required personalization behavior:",
            "- Weight recommendation and confidence toward what fits THIS investor, not a generic investor.",
            "- In profile_fit, explicitly connect the recommendation to their risk tolerance, goal, horizon, and experience.",
            "- If the stock is a poor fit for their profile, say so clearly even if the business looks strong in isolation.",
        ]
    )
    return "\n".join(lines)
