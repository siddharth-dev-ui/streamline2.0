"""
Streamline — AI-powered investment research platform.
Main Streamlit entry point.
"""

import streamlit as st

st.set_page_config(
    page_title="Streamline",
    page_icon="◯",
    layout="wide",
    initial_sidebar_state="expanded",
)

from data.profile_store import has_completed_onboarding
from utils.landing_page import render_landing, should_show_landing
from utils.loading import dismiss_boot_loader, show_boot_loader
from utils.theme import apply_theme, init_theme

if should_show_landing():
    render_landing()
    st.stop()

init_theme()

# Show on every run while content is building; auto-dismisses (max 4s failsafe).
show_boot_loader("Loading Streamline…")

completed = has_completed_onboarding()

if not completed:
    st.markdown(
        "<style>[data-testid='stSidebar'] { display: none; }</style>",
        unsafe_allow_html=True,
    )
    from utils.onboarding import render_onboarding

    render_onboarding()
else:
    from utils.ui import render_page, render_sidebar

    render_sidebar()
    render_page()

# Inject last so it overrides Streamlit's built-in theme CSS.
apply_theme(expand_sidebar=completed)
dismiss_boot_loader()
