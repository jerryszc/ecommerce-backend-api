"""App entrypoint: create tables (dev) and health check."""

from sqlmodel import SQLModel

import app.models  # noqa: F401  (register metadata)
from app.core.database import engine


def init_db() -> None:
    """Create tables directly. Production uses Alembic upgrades."""
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("Tables created (dev mode). Use Alembic in production.")
