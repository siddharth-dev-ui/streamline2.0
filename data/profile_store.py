"""Local persistence for the user investment profile."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from portfolio.profile import empty_profile, is_profile_complete, normalize_profile

DATA_DIR = Path(__file__).resolve().parent
PROFILE_PATH = DATA_DIR / "user_profile.json"


def load_profile() -> dict[str, Any]:
    """Load the user profile from disk, or return an empty profile."""
    if not PROFILE_PATH.exists():
        return empty_profile()

    try:
        with PROFILE_PATH.open(encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return empty_profile()

    if not isinstance(data, dict):
        return empty_profile()

    return normalize_profile(data)


def save_profile(profile: dict[str, Any]) -> None:
    """Persist the user profile to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = normalize_profile(profile)
    if is_profile_complete(payload):
        payload["onboarding_completed"] = True

    with PROFILE_PATH.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def has_completed_onboarding() -> bool:
    """Return whether the user has a completed onboarding profile."""
    profile = load_profile()
    return bool(profile.get("onboarding_completed")) and is_profile_complete(profile)


def clear_profile() -> None:
    """Remove the stored profile file."""
    if PROFILE_PATH.exists():
        PROFILE_PATH.unlink()
