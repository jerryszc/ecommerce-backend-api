"""FastAPI entrypoint: inventory and orders system."""

from fastapi import FastAPI
from sqlmodel import SQLModel

from app import models  # noqa: F401  (register metadata)
from app.api.routers import categories, customers, inventory, orders, products
from app.core.database import engine

app = FastAPI(title="Inventarios y Ordenes E-Commerce", version="0.1.0")

app.include_router(categories.router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(inventory.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


def init_db() -> None:
    """Create tables directly. Production uses Alembic upgrades."""
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
