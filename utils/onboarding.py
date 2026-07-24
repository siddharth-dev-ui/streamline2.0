"""First-time onboarding flow for Streamline."""

from __future__ import annotations

import streamlit as st

from data.profile_store import load_profile, save_profile
from portfolio.profile import generate_profile_summary
from utils.profile_form import render_profile_form

SUMMARY_KEY = "onboarding_awaiting_continue"


def render_onboarding() -> None:
    """Render the first-time onboarding questionnaire."""
    st.markdown(
        """
        <div class="onboarding-hero">
            <div class="logo-text">streamline</div>
            <div class="tagline">Set your profile once. We personalize everything after that.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 2, 1])
    with center:
        if st.session_state.get(SUMMARY_KEY):
            with st.container(border=True):
                st.markdown("### Your Investment Profile")
                st.markdown(generate_profile_summary(load_profile()))

            if st.button("Continue to Streamline", type="primary", use_container_width=True):
                del st.session_state[SUMMARY_KEY]
                st.rerun()
        else:
            payload = render_profile_form(key_prefix="onboarding", show_title=False)
            if payload:
                save_profile(payload)
                st.session_state[SUMMARY_KEY] = True
                st.rerun()
