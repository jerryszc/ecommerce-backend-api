"""Manejo de duplicados (409): SKU, email y categoria unicos."""

from fastapi.testclient import TestClient

from tests.conftest import make_customer, make_product


def test_duplicate_sku_returns_409(client: TestClient):
    """Arrange: producto creado. Act: re-crear mismo sku. Assert: 409."""
    first = make_product(client, stock=5)
    dup = {
        "sku": first["sku"],
        "name": "Duplicado",
        "description": "dup",
        "price": "10.00",
        "stock": 1,
        "is_active": True,
    }
    resp = client.post("/products", json=dup)
    assert resp.status_code == 409
    assert "SKU" in resp.json()["detail"]


def test_duplicate_email_returns_409(client: TestClient):
    """Arrange: customer creado. Act: re-crear mismo email. Assert: 409."""
    first = make_customer(client)
    resp = client.post(
        "/customers",
        json={"email": first["email"], "full_name": "Otro", "address": "X"},
    )
    assert resp.status_code == 409
    assert "Email" in resp.json()["detail"]


def test_duplicate_category_returns_409(client: TestClient):
    """Arrange: categoria creada. Act: duplicarla. Assert: 409."""
    arrange = client.post("/categories", json={"name": "Electronica", "description": "d"})
    assert arrange.status_code == 201
    act = client.post("/categories", json={"name": "Electronica", "description": "d2"})
    assert act.status_code == 409
    assert "Category" in act.json()["detail"]


def test_same_name_different_sku_ok(client: TestClient):
    """Arrange/Act/Assert: mismo name con distinto sku es valido (201)."""
    first = make_product(client, stock=1)
    payload = {
        "sku": first["sku"] + "-V2",
        "name": first["name"],  # name no es unique
        "description": "v2",
        "price": "10.00",
        "stock": 1,
        "is_active": True,
    }
    assert client.post("/products", json=payload).status_code == 201
