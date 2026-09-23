"""Integridad transaccional de ordenes: stock, rollback atomico y kardex."""

from fastapi.testclient import TestClient

from tests.conftest import make_customer, make_product


def test_create_order_happy_path_discounts_stock(client: TestClient):
    """Arrange: customer + 2 productos. Act: POST /orders. Assert: total, stock y OUT movements."""
    customer = make_customer(client)
    p1 = make_product(client, stock=10, price="10.00")
    p2 = make_product(client, stock=10, price="5.00")

    act = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "lines": [
                {"product_id": p1["id"], "quantity": 2},  # 20.00
                {"product_id": p2["id"], "quantity": 3},  # 15.00
            ],
        },
    )
    assert act.status_code == 201, act.text
    assert float(act.json()["total"]) == 35.00

    # Stock descontado.
    assert client.get(f"/products/{p1['id']}").json()["stock"] == 8
    assert client.get(f"/products/{p2['id']}").json()["stock"] == 7

    # Kardex: un OUT por linea con order_id enlazado.
    moves_p1 = client.get("/inventory/movements", params={"product_id": p1["id"]}).json()
    assert len(moves_p1) == 1
    assert moves_p1[0]["quantity_change"] == -2
    assert moves_p1[0]["quantity_after"] == 8
    assert moves_p1[0]["reason"] == "OUT"
    assert moves_p1[0]["order_id"] == act.json()["id"]


def test_order_insufficient_stock_single_line_rolls_back(client: TestClient):
    """Arrange: stock=2. Act: pedir 5. Assert: 400, stock=2, 0 ordenes, 0 movimientos."""
    customer = make_customer(client)
    product = make_product(client, stock=2, price="10.00")

    act = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "lines": [{"product_id": product["id"], "quantity": 5}],
        },
    )
    assert act.status_code == 400
    assert "Insufficient stock" in act.json()["detail"]

    # Rollback atomico: nada persistido.
    assert client.get(f"/products/{product['id']}").json()["stock"] == 2
    assert client.get("/orders").json() == []
    assert client.get("/inventory/movements", params={"product_id": product["id"]}).json() == []


def test_order_multi_line_atomic_rollback(client: TestClient):
    """Arrange: p1 stock=10, p2 stock=1. Act: orden [p1 x2 OK, p2 x5 FAIL]. Assert: rollback total."""
    customer = make_customer(client)
    p1 = make_product(client, stock=10, price="10.00")
    p2 = make_product(client, stock=1, price="10.00")

    act = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "lines": [
                {"product_id": p1["id"], "quantity": 2},
                {"product_id": p2["id"], "quantity": 5},
            ],
        },
    )
    assert act.status_code == 400, act.text

    # p1 NO debe descontarse aunque su linea era valida (atomicidad).
    assert client.get(f"/products/{p1['id']}").json()["stock"] == 10
    assert client.get(f"/products/{p2['id']}").json()["stock"] == 1
    assert client.get("/orders").json() == []
    assert client.get("/inventory/movements", params={"product_id": p1["id"]}).json() == []
    assert client.get("/inventory/movements", params={"product_id": p2["id"]}).json() == []


def test_order_inactive_product_rejected_and_no_side_effects(client: TestClient):
    """Arrange: producto inactivo. Act: ordenarlo. Assert: 400 y stock intacto."""
    customer = make_customer(client)
    product = make_product(client, stock=10)
    # Marcar inactivo directo en DB via API no existe: usar PUT interno no hay, recrear inactivo.
    resp = client.post(
        "/products",
        json={
            "sku": product["sku"] + "-INACT",
            "name": "Inactivo",
            "price": "9.99",
            "stock": 10,
            "is_active": False,
        },
    )
    inactive = resp.json()
    act = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "lines": [{"product_id": inactive["id"], "quantity": 1}],
        },
    )
    assert act.status_code == 400
    assert "inactive" in act.json()["detail"]
    assert client.get("/orders").json() == []


def test_order_product_not_found_returns_400(client: TestClient):
    """Arrange/Act/Assert: product_id inexistente → 400, sin ordenes."""
    customer = make_customer(client)
    act = client.post(
        "/orders",
        json={"customer_id": customer["id"], "lines": [{"product_id": 999999, "quantity": 1}]},
    )
    assert act.status_code == 400
    assert client.get("/orders").json() == []


def test_get_order_not_found_returns_404(client: TestClient):
    """Arrange/Act/Assert: GET /orders/999999 → 404 JSON, no traceback."""
    act = client.get("/orders/999999")
    assert act.status_code == 404
    assert "detail" in act.json()
