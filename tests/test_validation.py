"""Validaciones Pydantic (422): bad payloads nunca llegan a negocio/DB."""

from fastapi.testclient import TestClient

from tests.conftest import make_customer, make_product


def test_order_quantity_zero_returns_422(client: TestClient):
    """Arrange: customer + product. Act: quantity=0. Assert: 422."""
    customer = make_customer(client)
    product = make_product(client, stock=10)
    resp = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "lines": [{"product_id": product["id"], "quantity": 0}],
        },
    )
    assert resp.status_code == 422


def test_order_quantity_negative_returns_422(client: TestClient):
    """Arrange/Act/Assert: quantity=-1 rechazado por Field(gt=0)."""
    customer = make_customer(client)
    product = make_product(client, stock=10)
    resp = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "lines": [{"product_id": product["id"], "quantity": -5}],
        },
    )
    assert resp.status_code == 422


def test_order_empty_lines_returns_422(client: TestClient):
    """Arrange/Act/Assert: lines=[] viola min_length=1."""
    customer = make_customer(client)
    resp = client.post("/orders", json={"customer_id": customer["id"], "lines": []})
    assert resp.status_code == 422


def test_order_product_id_zero_returns_422(client: TestClient):
    """Arrange/Act/Assert: product_id=0 viola Field(gt=0)."""
    customer = make_customer(client)
    resp = client.post(
        "/orders", json={"customer_id": customer["id"], "lines": [{"product_id": 0, "quantity": 1}]}
    )
    assert resp.status_code == 422


def test_order_missing_fields_returns_422(client: TestClient):
    """Arrange/Act/Assert: payloads incompletos → 422, no 500."""
    assert client.post("/orders", json={}).status_code == 422
    assert client.post("/orders", json={"customer_id": 1}).status_code == 422
    assert client.post("/orders", json={"lines": []}).status_code == 422


def test_inventory_adjust_missing_quantity_returns_422(client: TestClient):
    """Arrange/Act/Assert: falta quantity_change → 422."""
    product = make_product(client, stock=5)
    resp = client.post("/inventory/adjust", json={"product_id": product["id"]})
    assert resp.status_code == 422


def test_inventory_adjust_product_id_zero_returns_422(client: TestClient):
    """Arrange/Act/Assert: product_id=0 viola Field(gt=0)."""
    resp = client.post("/inventory/adjust", json={"product_id": 0, "quantity_change": 5})
    assert resp.status_code == 422


def test_product_negative_price_returns_422(client: TestClient):
    """Arrange/Act/Assert: price<0 viola ge=0 -> 422."""
    resp = client.post(
        "/products",
        json={"sku": "NEG-PRICE", "name": "Bad", "price": "-1.00", "stock": 0},
    )
    assert resp.status_code == 422


def test_product_negative_stock_returns_422(client: TestClient):
    """Arrange/Act/Assert: stock<0 viola ge=0 -> 422."""
    resp = client.post(
        "/products",
        json={"sku": "NEG-STOCK", "name": "Bad", "price": "5.00", "stock": -3},
    )
    assert resp.status_code == 422
