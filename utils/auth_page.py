"""Sign-in / sign-up UI for Streamline."""

from __future__ import annotations

import json

import streamlit as st

from utils.auth import (
    begin_oauth,
    discord_configured,
    google_configured,
    login_with_email,
    register_with_email,
    remember_token_scripts,
    reset_password_with_email,
)
from utils.theme import get_theme


def _auth_styles(theme: dict) -> str:
    return f"""
    <style>
      [data-testid="stSidebar"],
      [data-testid="stHeader"],
      [data-testid="stToolbar"],
      [data-testid="stDecoration"],
      [data-testid="stStatusWidget"],
      #MainMenu, footer, .stDeployButton, .stAppDeployButton {{
        display: none !important;
      }}
      .block-container {{
        max-width: 420px !important;
        padding-top: 4rem !important;
        padding-bottom: 3rem !important;
      }}
      .sl-auth-wrap {{
        text-align: center;
        margin-bottom: 1.5rem;
      }}
      .sl-auth-brand {{
        font-family: "Instrument Serif", Georgia, serif;
        font-size: 2.5rem;
        font-weight: 400;
        letter-spacing: -0.03em;
        color: {theme["text"]};
        margin: 0 0 0.4rem;
      }}
      .sl-auth-sub {{
        color: {theme["text_muted"]};
        font-size: 0.95rem;
        margin: 0;
      }}
      .sl-auth-divider {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: {theme["text_muted"]};
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 1rem 0 0.85rem;
      }}
      .sl-auth-divider::before,
      .sl-auth-divider::after {{
        content: "";
        flex: 1;
        height: 1px;
        background: {theme["border"]};
      }}
    </style>
    """


def _redirect(url: str) -> None:
    st.html(
        f"""
<script>
(function () {{
  var url = {json.dumps(url)};
  try {{
    if (window.top && window.top !== window) {{ window.top.location.href = url; return; }}
  }} catch (e) {{}}
  window.location.href = url;
}})();
</script>
"""
    )


def render_auth_page() -> None:
    """Render a clean email/password + optional social sign-in."""
    theme = get_theme()
    st.markdown(_auth_styles(theme), unsafe_allow_html=True)

    pending = st.session_state.pop("pending_oauth_redirect", None)
    if pending:
        _redirect(str(pending))
        return

    st.markdown(
        """
        <div class="sl-auth-wrap">
          <p class="sl-auth-brand">streamline</p>
          <p class="sl-auth-sub">Welcome back</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    flash_error = st.session_state.pop("auth_flash_error", None)
    if flash_error:
        st.error(str(flash_error))

    mode = st.session_state.get("auth_ui_mode", "sign_in")

    google_ready = google_configured()
    discord_ready = discord_configured()
    social = []
    if google_ready:
        social.append("google")
    if discord_ready:
        social.append("discord")

    if social:
        cols = st.columns(len(social))
        for col, provider in zip(cols, social):
            with col:
                label = "Google" if provider == "google" else "Discord"
                if st.button(label, use_container_width=True, key=f"auth_{provider}_btn"):
                    try:
                        st.session_state["pending_oauth_redirect"] = begin_oauth(provider)
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
        st.markdown('<div class="sl-auth-divider">or</div>', unsafe_allow_html=True)

    if mode == "sign_in":
        with st.form("auth_sign_in_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Your password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            try:
                login_with_email(email=email, password=password)
                st.session_state["entered_app"] = True
                remember_token_scripts()
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Create account", use_container_width=True, key="goto_create"):
                st.session_state["auth_ui_mode"] = "create"
                st.rerun()
        with c2:
            if st.button("Reset password", use_container_width=True, key="goto_reset"):
                st.session_state["auth_ui_mode"] = "reset"
                st.rerun()

    elif mode == "create":
        with st.form("auth_create_form", clear_on_submit=False):
            name = st.text_input("Name", placeholder="Your name")
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="At least 8 characters")
            submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if submitted:
            try:
                register_with_email(email=email, password=password, name=name)
                st.session_state["entered_app"] = True
                remember_token_scripts()
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if st.button("Back to sign in", use_container_width=True, key="back_signin_create"):
            st.session_state["auth_ui_mode"] = "sign_in"
            st.rerun()

    else:  # reset
        with st.form("auth_reset_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("New password", type="password", placeholder="At least 8 characters")
            submitted = st.form_submit_button("Update password", type="primary", use_container_width=True)
        if submitted:
            try:
                reset_password_with_email(email=email, password=password)
                st.session_state["entered_app"] = True
                remember_token_scripts()
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if st.button("Back to sign in", use_container_width=True, key="back_signin_reset"):
            st.session_state["auth_ui_mode"] = "sign_in"
            st.rerun()
