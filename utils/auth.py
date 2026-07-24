"""Authentication helpers: email/password, Google, and Discord."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any
from urllib.parse import urlencode

import requests
import streamlit as st

from data.auth_store import (
    create_email_user,
    get_password_hash,
    get_user_by_email,
    init_auth_db,
    pop_oauth_state,
    save_oauth_state,
    upsert_oauth_user,
)

AUTH_USER_KEY = "auth_user"
SESSION_TOKEN_KEY = "auth_session_token"


def _secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except Exception:
        return default
    if value is None:
        return default
    return str(value).strip()


def _section_secret(section: str, key: str, default: str = "") -> str:
    try:
        block = st.secrets.get(section)
    except Exception:
        return default
    if block is None:
        return default
    try:
        value = block.get(key, default)  # type: ignore[union-attr]
    except Exception:
        return default
    if value is None:
        return default
    return str(value).strip()


def app_base_url() -> str:
    """Public base URL used for OAuth redirect_uri."""
    configured = _secret("APP_BASE_URL") or _section_secret("auth", "app_base_url")
    if configured:
        return configured.rstrip("/")
    # Local default — override in secrets for Streamlit Cloud.
    return "http://localhost:8501"


def google_configured() -> bool:
    return bool(
        (_section_secret("google", "client_id") or _secret("GOOGLE_CLIENT_ID"))
        and (_section_secret("google", "client_secret") or _secret("GOOGLE_CLIENT_SECRET"))
    )


def discord_configured() -> bool:
    return bool(
        (_section_secret("discord", "client_id") or _secret("DISCORD_CLIENT_ID"))
        and (_section_secret("discord", "client_secret") or _secret("DISCORD_CLIENT_SECRET"))
    )


def google_client_id() -> str:
    return _section_secret("google", "client_id") or _secret("GOOGLE_CLIENT_ID")


def google_client_secret() -> str:
    return _section_secret("google", "client_secret") or _secret("GOOGLE_CLIENT_SECRET")


def discord_client_id() -> str:
    return _section_secret("discord", "client_id") or _secret("DISCORD_CLIENT_ID")


def discord_client_secret() -> str:
    return _section_secret("discord", "client_secret") or _secret("DISCORD_CLIENT_SECRET")


def _cookie_secret() -> str:
    return (
        _secret("AUTH_COOKIE_SECRET")
        or _section_secret("auth", "cookie_secret")
        or "streamline-dev-cookie-secret-change-me"
    )


def _hash_password(password: str, *, salt: str | None = None) -> str:
    """Hash a password with PBKDF2-SHA256 (stdlib; no extra dependency)."""
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()
    return f"pbkdf2_sha256$200000${salt}${digest}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt, digest = stored.split("$", 3)
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(rounds),
    ).hex()
    return hmac.compare_digest(check, digest)


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "email": user.get("email") or "",
        "name": user.get("name") or "",
        "avatar_url": user.get("avatar_url") or "",
        "provider": user.get("provider") or "email",
    }


def get_current_user() -> dict[str, Any] | None:
    user = st.session_state.get(AUTH_USER_KEY)
    if isinstance(user, dict) and user.get("id"):
        return user
    return None


def is_authenticated() -> bool:
    return get_current_user() is not None


def set_current_user(user: dict[str, Any]) -> None:
    st.session_state[AUTH_USER_KEY] = _public_user(user)
    st.session_state[SESSION_TOKEN_KEY] = secrets.token_urlsafe(24)


def logout_user() -> None:
    st.session_state.pop(AUTH_USER_KEY, None)
    st.session_state.pop(SESSION_TOKEN_KEY, None)


def register_with_email(*, email: str, password: str, name: str = "") -> dict[str, Any]:
    init_auth_db()
    email_norm = email.strip().lower()
    if "@" not in email_norm or "." not in email_norm.split("@")[-1]:
        raise ValueError("Enter a valid email address.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    user = create_email_user(
        email=email_norm,
        password_hash=_hash_password(password),
        name=name or email_norm.split("@")[0],
    )
    set_current_user(user)
    return get_current_user()  # type: ignore[return-value]


def login_with_email(*, email: str, password: str) -> dict[str, Any]:
    init_auth_db()
    email_norm = email.strip().lower()
    stored = get_password_hash(email_norm)
    if not stored or not _verify_password(password, stored):
        raise ValueError("Incorrect email or password.")
    user = get_user_by_email(email_norm)
    if not user:
        raise ValueError("Incorrect email or password.")
    if user.get("provider") != "email" and not user.get("has_password"):
        raise ValueError("That email uses social sign-in. Continue with Google or Discord.")
    set_current_user(user)
    return get_current_user()  # type: ignore[return-value]


def _oauth_redirect_uri() -> str:
    return f"{app_base_url()}/"


def build_google_auth_url(state: str) -> str:
    params = {
        "client_id": google_client_id(),
        "redirect_uri": _oauth_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def build_discord_auth_url(state: str) -> str:
    params = {
        "client_id": discord_client_id(),
        "redirect_uri": _oauth_redirect_uri(),
        "response_type": "code",
        "scope": "identify email",
        "state": state,
        "prompt": "consent",
    }
    return f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"


def begin_oauth(provider: str) -> str:
    """Create CSRF state and return the provider authorize URL."""
    provider = provider.lower().strip()
    if provider == "google" and not google_configured():
        raise ValueError("Google sign-in is not configured. Add Google OAuth secrets.")
    if provider == "discord" and not discord_configured():
        raise ValueError("Discord sign-in is not configured. Add Discord OAuth secrets.")
    if provider not in {"google", "discord"}:
        raise ValueError("Unsupported provider.")

    state = secrets.token_urlsafe(24)
    save_oauth_state(state, provider)
    st.session_state["oauth_state"] = state
    st.session_state["oauth_provider"] = provider

    if provider == "google":
        return build_google_auth_url(state)
    return build_discord_auth_url(state)


def _exchange_google_code(code: str) -> dict[str, Any]:
    token_res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": google_client_id(),
            "client_secret": google_client_secret(),
            "redirect_uri": _oauth_redirect_uri(),
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    token_res.raise_for_status()
    tokens = token_res.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise ValueError("Google did not return an access token.")

    profile_res = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    profile_res.raise_for_status()
    profile = profile_res.json()
    return {
        "provider": "google",
        "provider_id": str(profile.get("sub") or ""),
        "email": profile.get("email"),
        "name": profile.get("name") or profile.get("given_name") or "",
        "avatar_url": profile.get("picture") or "",
    }


def _exchange_discord_code(code: str) -> dict[str, Any]:
    token_res = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": discord_client_id(),
            "client_secret": discord_client_secret(),
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _oauth_redirect_uri(),
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    token_res.raise_for_status()
    tokens = token_res.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise ValueError("Discord did not return an access token.")

    profile_res = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    profile_res.raise_for_status()
    profile = profile_res.json()
    user_id = str(profile.get("id") or "")
    avatar_hash = profile.get("avatar")
    avatar_url = ""
    if user_id and avatar_hash:
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
    name = profile.get("global_name") or profile.get("username") or ""
    return {
        "provider": "discord",
        "provider_id": user_id,
        "email": profile.get("email"),
        "name": name,
        "avatar_url": avatar_url,
    }


def _clear_oauth_query_params() -> None:
    try:
        for key in ("code", "state", "error", "error_description", "scope"):
            if key in st.query_params:
                del st.query_params[key]
    except Exception:
        pass


def process_oauth_callback() -> bool:
    """
    Handle OAuth redirect query params.

    Returns True when a login was completed (caller should st.rerun()).
    """
    params = st.query_params
    error = params.get("error")
    if isinstance(error, (list, tuple)):
        error = error[0] if error else None
    if error:
        st.session_state["auth_flash_error"] = (
            str(params.get("error_description") or error)
        )
        _clear_oauth_query_params()
        return False

    code = params.get("code")
    state = params.get("state")
    if isinstance(code, (list, tuple)):
        code = code[0] if code else None
    if isinstance(state, (list, tuple)):
        state = state[0] if state else None
    if not code or not state:
        return False

    provider = pop_oauth_state(str(state))
    if not provider:
        session_state = st.session_state.get("oauth_state")
        session_provider = st.session_state.get("oauth_provider")
        if session_state == state and session_provider:
            provider = str(session_provider)
        else:
            st.session_state["auth_flash_error"] = "Sign-in expired. Please try again."
            _clear_oauth_query_params()
            return False

    try:
        if provider == "google":
            identity = _exchange_google_code(str(code))
        elif provider == "discord":
            identity = _exchange_discord_code(str(code))
        else:
            raise ValueError("Unknown OAuth provider.")

        if not identity.get("provider_id"):
            raise ValueError("Provider did not return a user id.")

        user = upsert_oauth_user(
            provider=identity["provider"],
            provider_id=identity["provider_id"],
            email=identity.get("email"),
            name=identity.get("name") or "",
            avatar_url=identity.get("avatar_url") or "",
        )
        set_current_user(user)
        st.session_state["entered_app"] = True
        st.session_state["auth_flash_success"] = f"Signed in with {provider.title()}."
    except Exception as exc:
        st.session_state["auth_flash_error"] = f"Sign-in failed: {exc}"
    finally:
        st.session_state.pop("oauth_state", None)
        st.session_state.pop("oauth_provider", None)
        _clear_oauth_query_params()

    return is_authenticated()
