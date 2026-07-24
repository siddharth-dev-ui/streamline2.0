"""Resolve per-user data directories for authenticated sessions."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

DATA_DIR = Path(__file__).resolve().parent


def current_user_dir() -> Path:
    """Return the data directory for the signed-in user (or shared legacy dir)."""
    user = st.session_state.get("auth_user")
    if not isinstance(user, dict) or not user.get("id"):
        return DATA_DIR
    path = DATA_DIR / "users" / str(user["id"])
    path.mkdir(parents=True, exist_ok=True)
    return path
