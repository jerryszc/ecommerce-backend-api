"""Shared datetime helpers (naive UTC, no deprecated utcnow)."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return current UTC as naive datetime for DateTime columns."""
    return datetime.now(UTC).replace(tzinfo=None)
