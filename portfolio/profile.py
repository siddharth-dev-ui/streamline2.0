"""Investment profile schema, options, and summary generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

INVESTMENT_GOALS = [
    "Retirement",
    "Long-term growth",
    "Passive income",
    "Saving for a purchase",
    "General investing",
]

RISK_TOLERANCE_LEVELS = [
    "Very Conservative",
    "Conservative",
    "Moderate",
    "Growth",
    "Aggressive",
]

INVESTMENT_HORIZONS = [
    "Under 1 year",
    "1–3 years",
    "3–10 years",
    "10+ years",
]

EXPERIENCE_LEVELS = [
    "Beginner",
    "Intermediate",
    "Advanced",
]

SECTOR_OPTIONS = [
    "Technology",
    "Healthcare",
    "Financials",
    "Energy",
    "Consumer Discretionary",
    "Consumer Staples",
    "Industrials",
    "Real Estate",
    "Utilities",
    "Materials",
    "Communication Services",
]

PORTFOLIO_SIZE_OPTIONS = [
    "Prefer not to say",
    "Under $10,000",
    "$10,000 – $50,000",
    "$50,000 – $250,000",
    "$250,000 – $1,000,000",
    "Over $1,000,000",
]

PROFILE_FIELDS = (
    "investment_goal",
    "risk_tolerance",
    "investment_horizon",
    "experience",
    "preferred_sectors",
    "interest_in_etfs",
    "interest_in_dividends",
    "portfolio_size",
)


def empty_profile() -> dict[str, Any]:
    """Return a blank profile template."""
    return {
        "investment_goal": None,
        "risk_tolerance": None,
        "investment_horizon": None,
        "experience": None,
        "preferred_sectors": [],
        "interest_in_etfs": None,
        "interest_in_dividends": None,
        "portfolio_size": None,
        "onboarding_completed": False,
        "updated_at": None,
    }


def is_profile_complete(profile: dict[str, Any] | None) -> bool:
    """Check whether required onboarding fields are filled."""
    if not profile:
        return False

    required = (
        "investment_goal",
        "risk_tolerance",
        "investment_horizon",
        "experience",
    )
    return all(profile.get(field) is not None for field in required)


def normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Ensure profile has expected keys and types."""
    base = empty_profile()
    base.update({key: profile.get(key) for key in base})
    sectors = base.get("preferred_sectors") or []
    base["preferred_sectors"] = list(sectors)
    base["onboarding_completed"] = bool(profile.get("onboarding_completed")) and is_profile_complete(base)
    return base


def build_profile_payload(
    investment_goal: str,
    risk_tolerance: str,
    investment_horizon: str,
    experience: str,
    preferred_sectors: list[str],
    interest_in_etfs: bool,
    interest_in_dividends: bool,
    portfolio_size: str | None,
    onboarding_completed: bool = True,
) -> dict[str, Any]:
    """Build a profile dict ready for persistence."""
    return {
        "investment_goal": investment_goal,
        "risk_tolerance": risk_tolerance,
        "investment_horizon": investment_horizon,
        "experience": experience,
        "preferred_sectors": preferred_sectors,
        "interest_in_etfs": interest_in_etfs,
        "interest_in_dividends": interest_in_dividends,
        "portfolio_size": portfolio_size or "Prefer not to say",
        "onboarding_completed": onboarding_completed,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _goal_summary(goal: str) -> str:
    mapping = {
        "Retirement": "building long-term wealth for retirement",
        "Long-term growth": "maximizing long-term capital appreciation",
        "Passive income": "generating steady passive income",
        "Saving for a purchase": "saving toward a specific future purchase",
        "General investing": "pursuing flexible, general-purpose investing",
    }
    return mapping.get(goal, "pursuing your financial goals")


def _risk_summary(risk: str) -> str:
    mapping = {
        "Very Conservative": "capital preservation with minimal volatility",
        "Conservative": "modest growth with limited downside risk",
        "Moderate": "a balanced mix of growth and stability",
        "Growth": "higher growth potential with elevated volatility",
        "Aggressive": "maximum growth with a high tolerance for swings",
    }
    return mapping.get(risk, "a risk level aligned with your comfort")


def _horizon_summary(horizon: str) -> str:
    mapping = {
        "Under 1 year": "a short time horizon under one year",
        "1–3 years": "a near-term horizon of one to three years",
        "3–10 years": "a medium-term horizon of three to ten years",
        "10+ years": "a long-term horizon of ten years or more",
    }
    return mapping.get(horizon, "your stated time horizon")


def _experience_summary(experience: str) -> str:
    mapping = {
        "Beginner": "You're early in your investing journey, so clarity and education will matter.",
        "Intermediate": "You have foundational experience and can explore more nuanced strategies.",
        "Advanced": "You're an experienced investor comfortable evaluating complex opportunities.",
    }
    return mapping.get(experience, "")


def generate_profile_summary(profile: dict[str, Any]) -> str:
    """Generate a human-readable investment profile summary."""
    if not is_profile_complete(profile):
        return "Complete your profile to generate a personalized summary."

    goal = profile["investment_goal"]
    risk = profile["risk_tolerance"]
    horizon = profile["investment_horizon"]
    experience = profile["experience"]
    sectors = profile.get("preferred_sectors") or []
    etfs = profile["interest_in_etfs"]
    dividends = profile["interest_in_dividends"]
    portfolio_size = profile.get("portfolio_size")

    lines = [
        f"You're focused on **{_goal_summary(goal)}** with **{_risk_summary(risk)}**, "
        f"over **{_horizon_summary(horizon)}**.",
        _experience_summary(experience),
    ]

    if sectors:
        sector_list = ", ".join(sectors)
        lines.append(f"You're most interested in **{sector_list}**.")
    else:
        lines.append("You haven't narrowed in on specific sectors yet.")

    preferences = []
    if etfs:
        preferences.append("ETFs for diversified exposure")
    if dividends:
        preferences.append("dividend-focused investments")
    if preferences:
        lines.append("You're interested in " + " and ".join(preferences) + ".")
    else:
        lines.append("You prefer individual securities over broad ETF or dividend strategies for now.")

    if portfolio_size and portfolio_size != "Prefer not to say":
        lines.append(f"Your indicated portfolio size is **{portfolio_size}**.")
    else:
        lines.append("Portfolio size was not disclosed.")

    return "\n\n".join(line for line in lines if line)
