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

from data.auth_store import init_auth_db
from data.profile_store import has_completed_onboarding
from utils.auth import (
    is_authenticated,
    process_oauth_callback,
    process_remember_resume,
    remember_token_scripts,
    resume_bridge_script,
)
from utils.landing_page import render_landing, should_show_landing
from utils.loading import dismiss_boot_loader, show_boot_loader
from utils.theme import apply_theme, init_theme

init_auth_db()

if process_oauth_callback():
    remember_token_scripts()
    st.rerun()

if process_remember_resume():
    remember_token_scripts()
    st.rerun()

remember_token_scripts()

# Returning sessions resume before marketing ever paints.
if should_show_landing() and not is_authenticated():
    resume_bridge_script(force_app=True)
    render_landing()
    st.stop()

if not is_authenticated():
    init_theme()
    from utils.auth_page import render_auth_page

    resume_bridge_script(force_app=True)
    render_auth_page()
    apply_theme(expand_sidebar=False)
    st.stop()

init_theme()
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

apply_theme(expand_sidebar=completed)
dismiss_boot_loader()
