"""In-memory request history store.

Stores every recommendation request + response for audit trail.
In production this would be backed by a database; for the POC
a simple list with JSON file persistence is sufficient.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HISTORY_FILE = Path(__file__).resolve().parent.parent / "data" / "history.json"

_history: list[dict[str, Any]] = []
_counter: int = 0


def _load() -> None:
    """Load history from disk on first access."""
    global _history, _counter
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            _history = json.load(f)
        _counter = len(_history)


def _save() -> None:
    """Persist current history to disk."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(_history, f, indent=2, default=str)


def record(request: dict[str, Any], response: dict[str, Any]) -> str:
    """Record a request/response pair. Returns the request_id."""
    global _counter
    if not _history:
        _load()
    _counter += 1
    request_id = f"REQ-{_counter:04d}"
    entry = {
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": request,
        "response": response,
    }
    _history.append(entry)
    _save()
    return request_id


def get_all(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """Return paginated history entries (newest first)."""
    if not _history:
        _load()
    ordered = list(reversed(_history))
    page = ordered[offset : offset + limit]
    return {
        "total": len(_history),
        "limit": limit,
        "offset": offset,
        "entries": page,
    }


def get_by_id(request_id: str) -> dict[str, Any] | None:
    """Return a single history entry by request_id."""
    if not _history:
        _load()
    for entry in _history:
        if entry["request_id"] == request_id:
            return entry
    return None
