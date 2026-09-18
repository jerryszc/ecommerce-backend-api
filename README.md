# Sistema de Gestion de Inventarios y Ordenes E-Commerce

API para catalogo, inventario con kardex y ordenes con descuento atomico de stock.
Construida con FastAPI, SQLModel/SQLAlchemy, PostgreSQL y Pytest.

## Stack

- Python 3.10+ (type hints estrictos, PEP 8, UTF-8)
- FastAPI + Uvicorn
- SQLModel / SQLAlchemy (ORM, queries parametrizadas)
- Alembic (migraciones con autogenerate)
- PostgreSQL + psycopg2-binary
- pydantic-settings + `.env` (cero credenciales hardcodeadas)
- Pytest + TestClient (SQLite en memoria para tests)

## Funcionalidades MVP

- Catalogo: `Category 1---* Product` (SKU unico, precio/stock `>= 0`)
- Inventario: `StockMovement` (IN/OUT/ADJUST/RESERVE/RELEASE) + ajuste atomico
- Clientes y ordenes: `Customer 1---* Order 1---* OrderItem *---1 Product`
- `POST /orders` descuenta stock en transaccion (`SELECT ... FOR UPDATE`,
  valida activo/existencia/stock, crea items + movimiento OUT, calcula total)
- GETs con busqueda `q`, filtros (`category_id`, `is_active`, `min_price/max_price`,
  `customer_id`, `status`, `reason`) y paginacion (`skip`, `limit 1-100`)
- Seed idempotente y suite de 34 tests en verde sin warnings

## Estructura

```
app/
  main.py              # FastAPI app + /health
  seed.py              # python -m app.seed
  core/
    config.py          # Settings desde .env
    database.py        # engine + SessionLocal
    datetime.py        # utcnow() sin deprecacion
  models/
    category.py customer.py product.py
    order.py order_item.py stock_movement.py
  api/
    deps.py            # sesion por request
    routers/
      categories.py products.py customers.py
      orders.py inventory.py
  services/
    order_service.py   # create_order() atomico
  alembic/
    env.py versions/
tests/
  conftest.py test_orders.py test_inventory.py
  test_validation.py test_duplicates.py test_get_filters.py
```

## Instalacion

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` con tus credenciales locales (nunca commitees `.env`).

## Configuracion (.env)

| Variable | Ejemplo | Descripcion |
|---|---|---|
| DB_HOST | localhost | Host Postgres |
| DB_PORT | 5432 | Puerto Postgres |
| DB_NAME | proyecto_1 | Base de datos |
| DB_USER | postgres | Usuario |
| DB_PASSWORD | **** | Password (solo local) |

La URL se construye como
`postgresql+psycopg2://DB_USER:DB_PASSWORD@DB_HOST:DB_PORT/DB_NAME`.

## Base de datos y seed

```bash
alembic upgrade head
python -m app.seed
```

`alembic check` debe responder `No new upgrade operations detected`.
El seed es idempotente: 3 categorias, 4 productos, 1 cliente demo.

## Levantar la aplicacion

```bash
uvicorn app.main:app --reload --port 8000
```

- Salud: `http://127.0.0.1:8000/health`
- Docs: `http://127.0.0.1:8000/docs`
- Endpoints: `/categories`, `/products`, `/customers`, `/orders`, `/inventory/adjust`, `/inventory/movements`

## Suite de pruebas

```bash
pytest -v
```

34 tests: ordenes atomicas/rollback, inventario/kardex, duplicados 409,
validaciones 422, busquedas/filtros/paginacion. Config en `pytest.ini`
(solo silencia warnings de terceros `starlette`/`anyio`).

## Seguridad

- Secretos solo en `.env` via `pydantic-settings`
- Transacciones explicitas `commit/rollback` + `SELECT ... FOR UPDATE`
- Sin SQL crudo: todo via ORM parametrizado
