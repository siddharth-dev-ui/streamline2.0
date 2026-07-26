"""SQLite persistence for Streamline accounts."""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "auth.db"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db() -> None:
    """Create auth tables if they do not exist."""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT,
                name TEXT,
                avatar_url TEXT,
                provider TEXT NOT NULL DEFAULT 'email',
                provider_id TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                UNIQUE(provider, provider_id)
            );

            CREATE TABLE IF NOT EXISTS oauth_states (
                state TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS remember_tokens (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )


def _row_to_user(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"] or "",
        "avatar_url": row["avatar_url"] or "",
        "provider": row["provider"],
        "provider_id": row["provider_id"],
        "has_password": bool(row["password_hash"]),
        "created_at": row["created_at"],
    }


def get_user_by_email(email: str) -> dict[str, Any] | None:
    email_norm = email.strip().lower()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE lower(email) = ? LIMIT 1",
            (email_norm,),
        ).fetchone()
    return _row_to_user(row)


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ? LIMIT 1", (user_id,)).fetchone()
    return _row_to_user(row)


def get_user_by_provider(provider: str, provider_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE provider = ? AND provider_id = ? LIMIT 1",
            (provider, provider_id),
        ).fetchone()
    return _row_to_user(row)


def get_password_hash(email: str) -> str | None:
    email_norm = email.strip().lower()
    with _connect() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE lower(email) = ? LIMIT 1",
            (email_norm,),
        ).fetchone()
    if row is None:
        return None
    return row["password_hash"]


def get_user_auth_payload(user_id: str) -> dict[str, Any] | None:
    """Full auth fields for building a durable remember token."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ? LIMIT 1", (user_id,)).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"] or "",
        "avatar_url": row["avatar_url"] or "",
        "provider": row["provider"] or "email",
        "provider_id": row["provider_id"],
        "password_hash": row["password_hash"],
    }


def create_email_user(*, email: str, password_hash: str, name: str = "") -> dict[str, Any]:
    init_auth_db()
    email_norm = email.strip().lower()
    if get_user_by_email(email_norm):
        raise ValueError("An account with that email already exists.")
    now = time.time()
    user_id = str(uuid.uuid4())
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO users (id, email, password_hash, name, avatar_url, provider, provider_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, '', 'email', NULL, ?, ?)
                """,
                (user_id, email_norm, password_hash, name.strip(), now, now),
            )
    except sqlite3.Error as exc:
        raise RuntimeError(
            "Could not save your account. The app storage may be read-only — try again or contact the host."
        ) from exc
    user = get_user_by_id(user_id)
    if not user:
        raise RuntimeError("Failed to create user.")
    return user


def upsert_user_record(
    *,
    user_id: str,
    email: str | None,
    password_hash: str | None,
    name: str = "",
    avatar_url: str = "",
    provider: str = "email",
    provider_id: str | None = None,
) -> dict[str, Any]:
    """Insert or update a user row (used to restore accounts after ephemeral disk wipes)."""
    init_auth_db()
    now = time.time()
    email_norm = (email or "").strip().lower() or None
    existing = get_user_by_id(user_id) or (get_user_by_email(email_norm) if email_norm else None)
    if existing:
        with _connect() as conn:
            conn.execute(
                """
                UPDATE users
                SET email = COALESCE(?, email),
                    password_hash = COALESCE(?, password_hash),
                    name = CASE WHEN ? != '' THEN ? ELSE name END,
                    avatar_url = CASE WHEN ? != '' THEN ? ELSE avatar_url END,
                    provider = ?,
                    provider_id = COALESCE(?, provider_id),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    email_norm,
                    password_hash,
                    name,
                    name,
                    avatar_url,
                    avatar_url,
                    provider,
                    provider_id,
                    now,
                    existing["id"],
                ),
            )
        user = get_user_by_id(existing["id"])
    else:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO users (id, email, password_hash, name, avatar_url, provider, provider_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    email_norm,
                    password_hash,
                    name.strip(),
                    avatar_url,
                    provider,
                    provider_id,
                    now,
                    now,
                ),
            )
        user = get_user_by_id(user_id)
    if not user:
        raise RuntimeError("Failed to restore user.")
    return user


def update_email_password(*, email: str, password_hash: str, name: str = "") -> dict[str, Any]:
    """Set / reset the password for an existing email account."""
    init_auth_db()
    email_norm = email.strip().lower()
    user = get_user_by_email(email_norm)
    if not user:
        raise ValueError("No account found for that email.")
    now = time.time()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE users
            SET password_hash = ?,
                name = CASE WHEN ? != '' THEN ? ELSE name END,
                provider = 'email',
                updated_at = ?
            WHERE id = ?
            """,
            (password_hash, name.strip(), name.strip(), now, user["id"]),
        )
    updated = get_user_by_id(user["id"])
    if not updated:
        raise RuntimeError("Failed to update password.")
    return updated


def upsert_oauth_user(
    *,
    provider: str,
    provider_id: str,
    email: str | None,
    name: str = "",
    avatar_url: str = "",
) -> dict[str, Any]:
    """Create or update a user from an OAuth identity."""
    init_auth_db()
    existing = get_user_by_provider(provider, provider_id)
    now = time.time()
    email_norm = (email or "").strip().lower() or None

    if existing:
        with _connect() as conn:
            conn.execute(
                """
                UPDATE users
                SET email = COALESCE(?, email),
                    name = CASE WHEN ? != '' THEN ? ELSE name END,
                    avatar_url = CASE WHEN ? != '' THEN ? ELSE avatar_url END,
                    updated_at = ?
                WHERE id = ?
                """,
                (email_norm, name, name, avatar_url, avatar_url, now, existing["id"]),
            )
        user = get_user_by_id(existing["id"])
        if not user:
            raise RuntimeError("Failed to update OAuth user.")
        return user

    # Link by email when an email/password account already exists.
    if email_norm:
        by_email = get_user_by_email(email_norm)
        if by_email:
            with _connect() as conn:
                conn.execute(
                    """
                    UPDATE users
                    SET provider = ?, provider_id = ?,
                        name = CASE WHEN ? != '' THEN ? ELSE name END,
                        avatar_url = CASE WHEN ? != '' THEN ? ELSE avatar_url END,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        provider,
                        provider_id,
                        name,
                        name,
                        avatar_url,
                        avatar_url,
                        now,
                        by_email["id"],
                    ),
                )
            user = get_user_by_id(by_email["id"])
            if not user:
                raise RuntimeError("Failed to link OAuth user.")
            return user

    user_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO users (id, email, password_hash, name, avatar_url, provider, provider_id, created_at, updated_at)
            VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, email_norm, name.strip(), avatar_url, provider, provider_id, now, now),
        )
    user = get_user_by_id(user_id)
    if not user:
        raise RuntimeError("Failed to create OAuth user.")
    return user


def save_oauth_state(state: str, provider: str) -> None:
    init_auth_db()
    now = time.time()
    with _connect() as conn:
        conn.execute("DELETE FROM oauth_states WHERE created_at < ?", (now - 3600,))
        conn.execute(
            "INSERT OR REPLACE INTO oauth_states (state, provider, created_at) VALUES (?, ?, ?)",
            (state, provider, now),
        )


def pop_oauth_state(state: str) -> str | None:
    init_auth_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT provider, created_at FROM oauth_states WHERE state = ? LIMIT 1",
            (state,),
        ).fetchone()
        if row is None:
            return None
        conn.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
    if time.time() - float(row["created_at"]) > 3600:
        return None
    return str(row["provider"])


def create_remember_token(user_id: str, *, days: int = 30) -> str:
    """Create a remember-me token and return the raw token (show once)."""
    init_auth_db()
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    now = time.time()
    expires = now + days * 86400
    with _connect() as conn:
        conn.execute(
            "DELETE FROM remember_tokens WHERE user_id = ? OR expires_at < ?",
            (user_id, now),
        )
        conn.execute(
            """
            INSERT INTO remember_tokens (token_hash, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (token_hash, user_id, now, expires),
        )
    return raw


def get_user_for_remember_token(raw_token: str) -> dict[str, Any] | None:
    """Validate a remember-me token and return the user if valid."""
    init_auth_db()
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now = time.time()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT user_id, expires_at FROM remember_tokens
            WHERE token_hash = ? LIMIT 1
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        if float(row["expires_at"]) < now:
            conn.execute("DELETE FROM remember_tokens WHERE token_hash = ?", (token_hash,))
            return None
        user_id = str(row["user_id"])
    return get_user_by_id(user_id)


def revoke_remember_tokens(user_id: str | None = None, *, raw_token: str | None = None) -> None:
    init_auth_db()
    with _connect() as conn:
        if raw_token:
            token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
            conn.execute("DELETE FROM remember_tokens WHERE token_hash = ?", (token_hash,))
        if user_id:
            conn.execute("DELETE FROM remember_tokens WHERE user_id = ?", (user_id,))
