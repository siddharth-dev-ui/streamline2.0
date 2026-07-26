"""Shared investment profile questionnaire form."""

from __future__ import annotations

from typing import Any

import streamlit as st

from portfolio.profile import (
    EXPERIENCE_LEVELS,
    INVESTMENT_GOALS,
    INVESTMENT_HORIZONS,
    PORTFOLIO_SIZE_OPTIONS,
    RISK_TOLERANCE_LEVELS,
    SECTOR_OPTIONS,
    build_profile_payload,
)


def _default_index(options: list[str], value: str | None) -> int:
    if value in options:
        return options.index(value)
    return 0


def render_profile_form(
    profile: dict[str, Any] | None = None,
    *,
    key_prefix: str = "profile",
    show_title: bool = True,
    compact: bool = False,
    submit_label: str = "Save profile",
) -> dict[str, Any] | None:
    """
    Render the profile questionnaire.

    Returns a profile payload when the form is submitted, otherwise None.
    """
    profile = profile or {}

    if show_title:
        st.markdown(
            '<div class="section-title">Investment Profile</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-subtitle">Tell us about your goals so Streamline can tailor your experience.</div>',
            unsafe_allow_html=True,
        )

    with st.form(f"{key_prefix}_form"):
        st.markdown('<div class="form-section-label">Goals & Risk</div>', unsafe_allow_html=True)

        investment_goal = st.selectbox(
            "Investment goal",
            INVESTMENT_GOALS,
            index=_default_index(INVESTMENT_GOALS, profile.get("investment_goal")),
        )
        risk_tolerance = st.selectbox(
            "Risk tolerance",
            RISK_TOLERANCE_LEVELS,
            index=_default_index(RISK_TOLERANCE_LEVELS, profile.get("risk_tolerance")),
        )

        investment_horizon = st.selectbox(
            "Investment horizon",
            INVESTMENT_HORIZONS,
            index=_default_index(INVESTMENT_HORIZONS, profile.get("investment_horizon")),
        )
        experience = st.selectbox(
            "Experience",
            EXPERIENCE_LEVELS,
            index=_default_index(EXPERIENCE_LEVELS, profile.get("experience")),
        )

        if compact:
            preferred_sectors = profile.get("preferred_sectors") or []
            interest_in_etfs = bool(profile.get("interest_in_etfs", True))
            interest_in_dividends = bool(profile.get("interest_in_dividends", False))
            portfolio_size = profile.get("portfolio_size") or "Prefer not to say"
        else:
            st.markdown('<div class="form-section-label">Preferences</div>', unsafe_allow_html=True)

            preferred_sectors = st.multiselect(
                "Preferred sectors",
                SECTOR_OPTIONS,
                default=profile.get("preferred_sectors") or [],
            )

            col1, col2 = st.columns(2)
            with col1:
                interest_in_etfs = st.radio(
                    "Interest in ETFs",
                    options=[True, False],
                    format_func=lambda value: "Yes" if value else "No",
                    index=0 if profile.get("interest_in_etfs", True) else 1,
                    horizontal=True,
                )
            with col2:
                interest_in_dividends = st.radio(
                    "Interest in dividend investing",
                    options=[True, False],
                    format_func=lambda value: "Yes" if value else "No",
                    index=0 if profile.get("interest_in_dividends", False) else 1,
                    horizontal=True,
                )

            portfolio_size = st.selectbox(
                "Portfolio size (optional)",
                PORTFOLIO_SIZE_OPTIONS,
                index=_default_index(
                    PORTFOLIO_SIZE_OPTIONS,
                    profile.get("portfolio_size") or "Prefer not to say",
                ),
            )

        submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)

    if not submitted:
        return None

    return build_profile_payload(
        investment_goal=investment_goal,
        risk_tolerance=risk_tolerance,
        investment_horizon=investment_horizon,
        experience=experience,
        preferred_sectors=preferred_sectors,
        interest_in_etfs=interest_in_etfs,
        interest_in_dividends=interest_in_dividends,
        portfolio_size=portfolio_size,
    )
