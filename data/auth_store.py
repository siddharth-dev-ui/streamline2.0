"""SQLite persistence for Streamline accounts."""

from __future__ import annotations

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


def create_email_user(*, email: str, password_hash: str, name: str = "") -> dict[str, Any]:
    init_auth_db()
    email_norm = email.strip().lower()
    if get_user_by_email(email_norm):
        raise ValueError("An account with that email already exists.")
    now = time.time()
    user_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO users (id, email, password_hash, name, avatar_url, provider, provider_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, '', 'email', NULL, ?, ?)
            """,
            (user_id, email_norm, password_hash, name.strip(), now, now),
        )
    user = get_user_by_id(user_id)
    if not user:
        raise RuntimeError("Failed to create user.")
    return user


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
