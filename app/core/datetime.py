"""Shared datetime helpers (naive UTC, no deprecated utcnow)."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current UTC as naive datetime for DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
