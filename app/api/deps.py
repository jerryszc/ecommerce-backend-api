"""Shared API dependencies."""

from collections.abc import Generator

from sqlmodel import Session

from app.core.database import SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Provide a request-scoped session with rollback on error."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
