"""GET queries, filters and pagination: every list endpoint."""
from fastapi.testclient import TestClient

from tests.conftest import make_customer, make_product


def _make_category(client: TestClient, name: str) -> dict:
    resp = client.post("/categories", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_product_full(
    client: TestClient,
    sku: str,
    name: str,
    price: str = "10.00",
    stock: int = 10,
    category_id: int | None = None,
    is_active: bool = True,
) -> dict:
    payload: dict = {
        "sku": sku,
        "name": name,
        "price": price,
        "stock": stock,
        "is_active": is_active,
    }
    if category_id is not None:
        payload["category_id"] = category_id
    resp = client.post("/products", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_categories_search_q(client: TestClient):
    """Arrange: 2 categories. Act: q=Electr. Assert: solo 1."""
    _make_category(client, "Electronica QA")
    _make_category(client, "Hogar QA")
    resp = client.get("/categories", params={"q": "Electr"})
    assert resp.status_code == 200
    assert [c["name"] for c in resp.json()] == ["Electronica QA"]


def test_categories_pagination(client: TestClient):
    """Arrange: 3 categories. Act: limit=2 skip=1. Assert: pagina correcta."""
    for name in ["AAA QA", "BBB QA", "CCC QA"]:
        _make_category(client, name)
    page1 = client.get("/categories", params={"skip": 0, "limit": 2}).json()
    page2 = client.get("/categories", params={"skip": 2, "limit": 2}).json()
    assert [c["name"] for c in page1] == ["AAA QA", "BBB QA"]
    assert [c["name"] for c in page2] == ["CCC QA"]


def test_categories_invalid_pagination_422(client: TestClient):
    """Arrange/Act/Assert: limit=0 y skip=-1 violan Query ge -> 422."""
    assert client.get("/categories", params={"limit": 0}).status_code == 422
    assert client.get("/categories", params={"skip": -1}).status_code == 422


def test_products_search_by_sku_and_name(client: TestClient):
    """Arrange: 2 productos. Act: q por sku y por nombre. Assert: filtra."""
    _make_product_full(client, sku="MOUSE-001", name="Mouse Gamer")
    _make_product_full(client, sku="KEYB-001", name="Teclado Mec")
    by_sku = client.get("/products", params={"q": "MOUSE"}).json()
    by_name = client.get("/products", params={"q": "Teclado"}).json()
    assert [p["sku"] for p in by_sku] == ["MOUSE-001"]
    assert [p["sku"] for p in by_name] == ["KEYB-001"]


def test_products_filter_category_and_active(client: TestClient):
    """Arrange: categoria + activo/inactivo. Act: filtra. Assert: 1 cada uno."""
    cat = _make_category(client, "Cat Filter QA")
    _make_product_full(client, "ACT-001", "Activo", category_id=cat["id"], is_active=True)
    _make_product_full(client, "INA-001", "Inactivo", category_id=cat["id"], is_active=False)
    _make_product_full(client, "OTH-001", "Otro")
    by_cat = client.get("/products", params={"category_id": cat["id"]}).json()
    active = client.get("/products", params={"is_active": True}).json()
    inactive = client.get("/products", params={"is_active": False}).json()
    assert {p["sku"] for p in by_cat} == {"ACT-001", "INA-001"}
    assert "ACT-001" in {p["sku"] for p in active}
    assert [p["sku"] for p in inactive] == ["INA-001"]


def test_products_price_range_and_pagination(client: TestClient):
    """Arrange: precios 10/50/90. Act: min/max + skip/limit. Assert: rangos."""
    _make_product_full(client, "P-010", "Barato", price="10.00")
    _make_product_full(client, "P-050", "Medio", price="50.00")
    _make_product_full(client, "P-090", "Caro", price="90.00")
    mid = client.get("/products", params={"min_price": "20.00", "max_price": "60.00"}).json()
    assert [p["sku"] for p in mid] == ["P-050"]
    page = client.get("/products", params={"skip": 1, "limit": 1}).json()
    assert len(page) == 1
    assert client.get("/products", params={"limit": 101}).status_code == 422


def test_customers_search_and_pagination(client: TestClient):
    """Arrange: 2 clientes. Act: q + paginacion. Assert: filtra y pagina."""
    make_customer(client)
    resp = client.post(
        "/customers",
        json={"email": "ana.qa@example.com", "full_name": "Ana QA"},
    )
    assert resp.status_code == 201
    found = client.get("/customers", params={"q": "ana.qa"}).json()
    assert len(found) == 1 and found[0]["email"] == "ana.qa@example.com"
    page = client.get("/customers", params={"skip": 0, "limit": 1}).json()
    assert len(page) == 1


def test_orders_filter_by_customer_and_status(client: TestClient):
    """Arrange: 2 clientes con 1 orden cada uno. Act: filtra. Assert: 1-1."""
    c1 = make_customer(client)
    c2 = make_customer(client)
    p1 = make_product(client, stock=10)
    p2 = make_product(client, stock=10)
    r1 = client.post(
        "/orders",
        json={"customer_id": c1["id"], "lines": [{"product_id": p1["id"], "quantity": 1}]},
    )
    r2 = client.post(
        "/orders",
        json={"customer_id": c2["id"], "lines": [{"product_id": p2["id"], "quantity": 1}]},
    )
    assert r1.status_code == 201 and r2.status_code == 201
    only_c1 = client.get("/orders", params={"customer_id": c1["id"]}).json()
    assert [o["id"] for o in only_c1] == [r1.json()["id"]]
    pending = client.get("/orders", params={"status": "pending"}).json()
    assert {o["id"] for o in pending} == {r1.json()["id"], r2.json()["id"]}
    page = client.get("/orders", params={"skip": 1, "limit": 1}).json()
    assert len(page) == 1


def test_movements_filter_by_reason_and_pagination(client: TestClient):
    """Arrange: IN (+5) y OUT (orden -1). Act: filtra por reason. Assert."""
    product = make_product(client, stock=10)
    customer = make_customer(client)
    client.post(
        "/inventory/adjust",
        json={"product_id": product["id"], "quantity_change": 5, "reason": "IN"},
    )
    client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "lines": [{"product_id": product["id"], "quantity": 1}],
        },
    )
    ins = client.get("/inventory/movements", params={"reason": "IN"}).json()
    outs = client.get("/inventory/movements", params={"reason": "OUT"}).json()
    by_product = client.get(
        "/inventory/movements", params={"product_id": product["id"]}
    ).json()
    assert len(ins) >= 1 and all(m["reason"] == "IN" for m in ins)
    assert len(outs) == 1 and outs[0]["quantity_change"] == -1
    assert len(by_product) == len(ins) + len(outs)
    page = client.get("/inventory/movements", params={"skip": 0, "limit": 1}).json()
    assert len(page) == 1
