"""Integracion inventario: ajuste de stock + kardex (StockMovement)."""

from fastapi.testclient import TestClient

from tests.conftest import make_product


def test_adjust_in_increases_stock_and_kardex(client: TestClient):
    """Arrange: stock=10. Act: POST /inventory/adjust +5. Assert: stock=15 y quantity_after=15."""
    product = make_product(client, stock=10)
    act = client.post(
        "/inventory/adjust",
        json={"product_id": product["id"], "quantity_change": 5, "reason": "IN"},
    )
    assert act.status_code == 201, act.text
    movement = act.json()
    assert movement["quantity_change"] == 5
    assert movement["quantity_after"] == 15
    assert client.get(f"/products/{product['id']}").json()["stock"] == 15


def test_adjust_out_decreases_stock(client: TestClient):
    """Arrange: stock=10. Act: -4 OUT. Assert: stock=6, reason OUT."""
    product = make_product(client, stock=10)
    act = client.post(
        "/inventory/adjust",
        json={"product_id": product["id"], "quantity_change": -4, "reason": "OUT"},
    )
    assert act.status_code == 201
    assert act.json()["quantity_after"] == 6
    assert client.get(f"/products/{product['id']}").json()["stock"] == 6


def test_adjust_zero_returns_400(client: TestClient):
    """Arrange/Act/Assert: quantity_change=0 → 400, stock intacto."""
    product = make_product(client, stock=7)
    act = client.post("/inventory/adjust", json={"product_id": product["id"], "quantity_change": 0})
    assert act.status_code == 400
    assert client.get(f"/products/{product['id']}").json()["stock"] == 7


def test_adjust_insufficient_stock_returns_400_and_no_movement(client: TestClient):
    """Arrange: stock=3. Act: -5. Assert: 400, stock=3, sin movimientos."""
    product = make_product(client, stock=3)
    act = client.post(
        "/inventory/adjust", json={"product_id": product["id"], "quantity_change": -5}
    )
    assert act.status_code == 400
    assert "Insufficient stock" in act.json()["detail"]
    assert client.get(f"/products/{product['id']}").json()["stock"] == 3
    assert client.get("/inventory/movements", params={"product_id": product["id"]}).json() == []


def test_adjust_product_not_found_returns_404(client: TestClient):
    """Arrange/Act/Assert: product_id inexistente → 404."""
    act = client.post("/inventory/adjust", json={"product_id": 999999, "quantity_change": 1})
    assert act.status_code == 404


def test_movements_filter_by_product(client: TestClient):
    """Arrange: 2 productos con 1 ajuste c/u. Act: GET filtrado. Assert: solo 1 por producto."""
    p1 = make_product(client, stock=5)
    p2 = make_product(client, stock=5)
    client.post("/inventory/adjust", json={"product_id": p1["id"], "quantity_change": 1})
    client.post("/inventory/adjust", json={"product_id": p2["id"], "quantity_change": 2})
    only_p1 = client.get("/inventory/movements", params={"product_id": p1["id"]}).json()
    assert len(only_p1) == 1
    assert only_p1[0]["product_id"] == p1["id"]
