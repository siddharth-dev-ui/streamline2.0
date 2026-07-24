"""Sign-in / sign-up UI for Streamline."""

from __future__ import annotations

import json

import streamlit as st

from utils.auth import (
    begin_oauth,
    discord_configured,
    get_current_user,
    google_configured,
    login_with_email,
    register_with_email,
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
        max-width: 480px !important;
        padding-top: 3.5rem !important;
        padding-bottom: 3rem !important;
      }}
      .sl-auth-wrap {{
        text-align: center;
        margin-bottom: 1.25rem;
      }}
      .sl-auth-brand {{
        font-family: "Instrument Serif", Georgia, serif;
        font-size: 2.4rem;
        font-weight: 400;
        letter-spacing: -0.03em;
        color: {theme["text"]};
        margin: 0 0 0.35rem;
      }}
      .sl-auth-sub {{
        color: {theme["text_muted"]};
        font-size: 0.98rem;
        margin: 0;
      }}
      .sl-auth-divider {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: {theme["text_muted"]};
        font-size: 0.8rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin: 0.35rem 0 0.85rem;
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
    """Navigate the app window to an external OAuth provider."""
    st.html(
        f"""
<script>
(function () {{
  var url = {json.dumps(url)};
  try {{
    if (window.top && window.top !== window) {{
      window.top.location.href = url;
      return;
    }}
  }} catch (e) {{}}
  window.location.href = url;
}})();
</script>
"""
    )


def render_auth_page() -> None:
    """Render email/password + social sign-in."""
    theme = get_theme()
    st.markdown(_auth_styles(theme), unsafe_allow_html=True)

    pending = st.session_state.pop("pending_oauth_redirect", None)
    if pending:
        st.info("Redirecting to sign in…")
        _redirect(str(pending))
        return

    st.markdown(
        """
        <div class="sl-auth-wrap">
          <p class="sl-auth-brand">streamline</p>
          <p class="sl-auth-sub">Sign in to continue to your research workspace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    flash_error = st.session_state.pop("auth_flash_error", None)
    flash_ok = st.session_state.pop("auth_flash_success", None)
    if flash_error:
        st.error(str(flash_error))
    if flash_ok:
        st.success(str(flash_ok))

    mode = st.radio(
        "Mode",
        ["Sign in", "Create account"],
        horizontal=True,
        label_visibility="collapsed",
        key="auth_mode_radio",
    )

    with st.form("email_auth_form", clear_on_submit=False):
        name = ""
        if mode == "Create account":
            name = st.text_input("Name", placeholder="Your name")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="At least 8 characters")
        submitted = st.form_submit_button(
            "Create account" if mode == "Create account" else "Sign in",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            if mode == "Create account":
                register_with_email(email=email, password=password, name=name)
            else:
                login_with_email(email=email, password=password)
            st.session_state["entered_app"] = True
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Something went wrong. Please try again.")

    st.markdown('<div class="sl-auth-divider">or continue with</div>', unsafe_allow_html=True)

    g_col, d_col = st.columns(2)
    with g_col:
        google_ready = google_configured()
        if st.button(
            "Google",
            use_container_width=True,
            disabled=not google_ready,
            key="auth_google_btn",
        ):
            try:
                st.session_state["pending_oauth_redirect"] = begin_oauth("google")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if not google_ready:
            st.caption("Add Google OAuth secrets to enable.")

    with d_col:
        discord_ready = discord_configured()
        if st.button(
            "Discord",
            use_container_width=True,
            disabled=not discord_ready,
            key="auth_discord_btn",
        ):
            try:
                st.session_state["pending_oauth_redirect"] = begin_oauth("discord")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if not discord_ready:
            st.caption("Add Discord OAuth secrets to enable.")

    if get_current_user():
        st.info("You are signed in.")
