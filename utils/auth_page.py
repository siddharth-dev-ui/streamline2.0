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


def _autofill_bridge() -> None:
    """
    Detect browser password autofill, sync values into Streamlit widgets,
    then click Sign in so the user lands in the app without an extra click.
    """
    st.html(
        """
<script>
(function () {
  if (window.__streamlineAuthAutofill) return;
  window.__streamlineAuthAutofill = true;

  function notifyReact(el) {
    if (!el) return;
    try {
      var tracker = el._valueTracker;
      if (tracker) tracker.setValue("");
    } catch (e) {}
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function findFields(doc) {
    var inputs = Array.prototype.slice.call(doc.querySelectorAll("input"));
    var password = inputs.find(function (el) {
      return el.type === "password" && el.offsetParent !== null;
    });
    if (!password) return null;
    var email = null;
    for (var i = 0; i < inputs.length; i++) {
      var el = inputs[i];
      if (el === password) continue;
      if (el.offsetParent === null) continue;
      var type = (el.type || "text").toLowerCase();
      var auto = (el.autocomplete || "").toLowerCase();
      var name = ((el.name || "") + " " + (el.id || "") + " " + (el.placeholder || "")).toLowerCase();
      if (
        type === "email" ||
        type === "text" ||
        auto.indexOf("username") >= 0 ||
        auto.indexOf("email") >= 0 ||
        name.indexOf("email") >= 0
      ) {
        email = el;
        break;
      }
    }
    return email && password ? { email: email, password: password } : null;
  }

  function isSignInMode(doc) {
    var checked = doc.querySelector('[role="radiogroup"] input:checked, [data-baseweb="radio"] input:checked');
    if (checked) {
      var label = (checked.parentElement && checked.parentElement.textContent) || "";
      if (/create account/i.test(label)) return false;
      if (/sign in/i.test(label)) return true;
    }
    // Default radio order: Sign in first.
    return true;
  }

  function findSignInButton(doc) {
    var buttons = Array.prototype.slice.call(doc.querySelectorAll("button"));
    return buttons.find(function (btn) {
      var text = (btn.textContent || "").trim().toLowerCase();
      return text === "sign in" && !btn.disabled;
    });
  }

  function isAutofilled(el) {
    if (!el) return false;
    try {
      if (el.matches(":-webkit-autofill") || el.matches(":autofill")) return true;
    } catch (e) {}
    return el.dataset.slAutofilled === "1";
  }

  function markAutofillListeners(doc) {
    var fields = findFields(doc);
    if (!fields) return;
    [fields.email, fields.password].forEach(function (el) {
      if (!el || el.dataset.slAutofillBound === "1") return;
      el.dataset.slAutofillBound = "1";
      el.addEventListener("animationstart", function (event) {
        if (event && /onAutoFillStart/i.test(event.animationName || "")) {
          el.dataset.slAutofilled = "1";
        }
      });
    });
  }

  function tryAutofillLogin(doc) {
    if (!isSignInMode(doc)) return false;
    markAutofillListeners(doc);
    var fields = findFields(doc);
    if (!fields) return false;
    var email = (fields.email.value || "").trim();
    var password = fields.password.value || "";
    if (!email || password.length < 8) return false;
    // Only auto-submit when the browser password manager filled the fields.
    if (!isAutofilled(fields.email) && !isAutofilled(fields.password)) return false;

    fields.email.setAttribute("autocomplete", "username");
    fields.password.setAttribute("autocomplete", "current-password");
    notifyReact(fields.email);
    notifyReact(fields.password);

    var btn = findSignInButton(doc);
    if (!btn) return false;
    if (btn.getAttribute("data-sl-autofill-clicked") === "1") return true;
    btn.setAttribute("data-sl-autofill-clicked", "1");
    setTimeout(function () { btn.click(); }, 150);
    return true;
  }

  function scan() {
    var docs = [document];
    try {
      if (window.parent && window.parent.document) docs.push(window.parent.document);
    } catch (e) {}
    for (var i = 0; i < docs.length; i++) {
      try {
        if (tryAutofillLogin(docs[i])) return true;
      } catch (err) {}
    }
    return false;
  }

  var tries = 0;
  var timer = setInterval(function () {
    tries += 1;
    if (scan() || tries > 24) clearInterval(timer);
  }, 300);

  // Chrome autofill sometimes paints without firing input events.
  try {
    document.addEventListener("animationstart", function (event) {
      if (!event || !event.animationName) return;
      if (/onAutoFillStart/i.test(event.animationName)) scan();
    }, true);
  } catch (e) {}
})();
</script>
"""
    )


def render_auth_page() -> None:
    """Render email/password + social sign-in."""
    theme = get_theme()
    st.markdown(_auth_styles(theme), unsafe_allow_html=True)
    _autofill_bridge()

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

    # Non-form inputs so browser autofill can sync into Streamlit and auto-submit.
    name = ""
    if mode == "Create account":
        name = st.text_input("Name", placeholder="Your name", key="auth_name")
    email = st.text_input(
        "Email",
        placeholder="you@example.com",
        key="auth_email",
    )
    password = st.text_input(
        "Password",
        type="password",
        placeholder="At least 8 characters",
        key="auth_password",
    )

    submitted = st.button(
        "Create account" if mode == "Create account" else "Sign in",
        type="primary",
        use_container_width=True,
        key="auth_submit",
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
