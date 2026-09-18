"""Shared Pytest fixtures: isolated SQLite + TestClient (AAA support)."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  (register metadata for create_all)
from app.api.deps import get_session
from app.main import app

# Single in-memory SQLite shared via StaticPool (one connection for all threads).
engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_session_override():
    """Request-scoped session against SQLite with commit/rollback."""
    session = Session(engine_test)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


app.dependency_overrides[get_session] = get_session_override


@pytest.fixture()
def client():
    """Fresh DB tables + TestClient per test for full isolation."""
    SQLModel.metadata.drop_all(engine_test)
    SQLModel.metadata.create_all(engine_test)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides[get_session] = get_session_override


def _unique(prefix: str) -> str:
    """Unique suffix to avoid collisions between tests."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def customer(client: TestClient) -> dict:
    """Arrange helper: create one customer via POST /customers."""
    payload = {
        "email": f"{_unique('qa')}@example.com",
        "full_name": "QA Customer",
        "address": "Calle 123",
    }
    resp = client.post("/customers", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def product(client: TestClient) -> dict:
    """Arrange helper: create one product with stock=10 via POST /products."""
    payload = {
        "sku": _unique("SKU"),
        "name": "Widget QA",
        "description": "Producto para pruebas",
        "price": "25.00",
        "stock": 10,
        "is_active": True,
    }
    resp = client.post("/products", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def make_product(client: TestClient, stock: int = 10, price: str = "10.00") -> dict:
    """Create an extra product with custom stock/price."""
    payload = {
        "sku": _unique("SKU"),
        "name": "Widget QA",
        "description": "extra",
        "price": price,
        "stock": stock,
        "is_active": True,
    }
    resp = client.post("/products", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def make_customer(client: TestClient) -> dict:
    """Create an extra customer."""
    payload = {
        "email": f"{_unique('qa')}@example.com",
        "full_name": "QA Extra",
        "address": "Av 456",
    }
    resp = client.post("/customers", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
