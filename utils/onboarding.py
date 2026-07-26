"""First-time onboarding flow for Streamline."""

from __future__ import annotations

import streamlit as st

from data.profile_store import save_profile
from utils.profile_form import render_profile_form


def render_onboarding() -> None:
    """Render a short first-run profile setup, then enter the app."""
    st.markdown(
        """
        <div class="onboarding-hero">
            <div class="logo-text">streamline</div>
            <div class="tagline">A few preferences so research fits you.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 2, 1])
    with center:
        payload = render_profile_form(
            key_prefix="onboarding",
            show_title=False,
            compact=True,
            submit_label="Continue",
        )
        if payload:
            save_profile(payload)
            st.rerun()
