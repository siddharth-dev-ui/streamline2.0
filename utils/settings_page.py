"""Settings page for Streamline."""

from __future__ import annotations

import streamlit as st

from data.profile_store import load_profile, save_profile
from portfolio.profile import generate_profile_summary
from utils.profile_form import render_profile_form


def render_settings() -> None:
    """Render the settings page with profile summary and edit form."""
    st.markdown(
        """
        <div class="page-header">
            <div class="page-title">Settings</div>
            <div class="page-subtitle">Manage your investment profile and preferences.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    profile = load_profile()

    with st.container(border=True):
        st.markdown("### Current Profile Summary")
        st.markdown(generate_profile_summary(profile))

    payload = render_profile_form(profile, key_prefix="settings", show_title=True)
    if payload:
        save_profile(payload)
        st.success("Your investment profile has been updated.")
        st.rerun()
