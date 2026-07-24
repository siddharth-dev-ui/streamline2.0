"""Local persistence for user watchlists.

Designed as a thin repository layer so a database backend can replace
file I/O later without changing page/call sites.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent
WATCHLIST_PATH = DATA_DIR / "watchlists.json"


def _watchlist_path() -> Path:
    from data.paths import current_user_dir

    path = current_user_dir() / "watchlists.json"
    if not path.exists() and WATCHLIST_PATH.exists() and path != WATCHLIST_PATH:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(WATCHLIST_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        except OSError:
            pass
    return path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_store() -> dict[str, Any]:
    return {"watchlists": [], "active_id": None, "updated_at": None}


def _slug_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name.strip())
    if not cleaned:
        raise ValueError("Watchlist name is required.")
    if len(cleaned) > 48:
        raise ValueError("Watchlist name must be 48 characters or fewer.")
    return cleaned


def _normalize_watchlist(item: dict[str, Any]) -> dict[str, Any]:
    tickers_raw = item.get("tickers") or []
    tickers: list[str] = []
    seen: set[str] = set()
    for ticker in tickers_raw:
        symbol = str(ticker).upper().strip()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        tickers.append(symbol)

    return {
        "id": str(item.get("id") or uuid.uuid4()),
        "name": _slug_name(str(item.get("name") or "Watchlist")),
        "tickers": tickers,
        "created_at": item.get("created_at") or _now(),
        "updated_at": item.get("updated_at") or _now(),
    }


def load_store() -> dict[str, Any]:
    """Load the full watchlist store from disk."""
    path = _watchlist_path()
    if not path.exists():
        return _empty_store()

    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return _empty_store()

    if not isinstance(data, dict):
        return _empty_store()

    watchlists = []
    for item in data.get("watchlists") or []:
        if not isinstance(item, dict):
            continue
        try:
            watchlists.append(_normalize_watchlist(item))
        except (TypeError, ValueError):
            continue

    active_id = data.get("active_id")
    if active_id and not any(item["id"] == active_id for item in watchlists):
        active_id = watchlists[0]["id"] if watchlists else None
    if not active_id and watchlists:
        active_id = watchlists[0]["id"]

    return {
        "watchlists": watchlists,
        "active_id": active_id,
        "updated_at": data.get("updated_at"),
    }


def save_store(store: dict[str, Any]) -> None:
    """Persist the watchlist store."""
    path = _watchlist_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    watchlists = [_normalize_watchlist(item) for item in store.get("watchlists") or []]
    active_id = store.get("active_id")
    if active_id and not any(item["id"] == active_id for item in watchlists):
        active_id = watchlists[0]["id"] if watchlists else None

    payload = {
        "watchlists": watchlists,
        "active_id": active_id,
        "updated_at": _now(),
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def list_watchlists() -> list[dict[str, Any]]:
    return load_store()["watchlists"]


def get_active_watchlist() -> dict[str, Any] | None:
    store = load_store()
    active_id = store.get("active_id")
    for item in store["watchlists"]:
        if item["id"] == active_id:
            return item
    return store["watchlists"][0] if store["watchlists"] else None


def set_active_watchlist(watchlist_id: str) -> None:
    store = load_store()
    if not any(item["id"] == watchlist_id for item in store["watchlists"]):
        raise ValueError("Watchlist not found.")
    store["active_id"] = watchlist_id
    save_store(store)


def create_watchlist(name: str) -> dict[str, Any]:
    store = load_store()
    cleaned = _slug_name(name)
    for item in store["watchlists"]:
        if item["name"].lower() == cleaned.lower():
            raise ValueError(f"A watchlist named '{cleaned}' already exists.")

    watchlist = {
        "id": str(uuid.uuid4()),
        "name": cleaned,
        "tickers": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    store["watchlists"].append(watchlist)
    store["active_id"] = watchlist["id"]
    save_store(store)
    return watchlist


def rename_watchlist(watchlist_id: str, name: str) -> dict[str, Any]:
    store = load_store()
    cleaned = _slug_name(name)
    target = None
    for item in store["watchlists"]:
        if item["id"] == watchlist_id:
            target = item
        elif item["name"].lower() == cleaned.lower():
            raise ValueError(f"A watchlist named '{cleaned}' already exists.")

    if target is None:
        raise ValueError("Watchlist not found.")

    target["name"] = cleaned
    target["updated_at"] = _now()
    save_store(store)
    return target


def delete_watchlist(watchlist_id: str) -> None:
    store = load_store()
    remaining = [item for item in store["watchlists"] if item["id"] != watchlist_id]
    if len(remaining) == len(store["watchlists"]):
        raise ValueError("Watchlist not found.")

    store["watchlists"] = remaining
    if store.get("active_id") == watchlist_id:
        store["active_id"] = remaining[0]["id"] if remaining else None
    save_store(store)


def add_ticker(watchlist_id: str, ticker: str) -> dict[str, Any]:
    symbol = str(ticker).upper().strip()
    if not symbol:
        raise ValueError("Enter a ticker symbol.")

    store = load_store()
    target = None
    for item in store["watchlists"]:
        if item["id"] == watchlist_id:
            target = item
            break
    if target is None:
        raise ValueError("Watchlist not found.")

    if symbol in target["tickers"]:
        raise ValueError(f"{symbol} is already on this watchlist.")

    target["tickers"].append(symbol)
    target["updated_at"] = _now()
    save_store(store)
    return target


def remove_ticker(watchlist_id: str, ticker: str) -> dict[str, Any]:
    symbol = str(ticker).upper().strip()
    store = load_store()
    target = None
    for item in store["watchlists"]:
        if item["id"] == watchlist_id:
            target = item
            break
    if target is None:
        raise ValueError("Watchlist not found.")

    if symbol not in target["tickers"]:
        raise ValueError(f"{symbol} is not on this watchlist.")

    target["tickers"] = [item for item in target["tickers"] if item != symbol]
    target["updated_at"] = _now()
    save_store(store)
    return target
