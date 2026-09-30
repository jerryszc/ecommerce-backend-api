# E-Commerce Backend API — Inventory & Orders

**[Versión en español →](README.md)**

Transactional e-commerce API with row-level concurrency control, an inventory kardex, and
atomicity guarantees on order creation.

[![Live](https://img.shields.io/badge/live-ecommerce--backend--api--sh6c.onrender.com-brightgreen)](https://ecommerce-backend-api-sh6c.onrender.com/health)
[![CI](https://github.com/jerryszc/ecommerce-backend-api/actions/workflows/ci.yml/badge.svg)](https://github.com/jerryszc/ecommerce-backend-api/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688.svg)](https://fastapi.tiangolo.com/)
[![MyPy strict](https://img.shields.io/badge/mypy-strict%20%7C%20passed-brightgreen.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-34%20passing%20%7C%20coverage%20gate%2080%25-brightgreen.svg)](tests)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Stack:** Python 3.11 · FastAPI · SQLModel · SQLAlchemy · PostgreSQL 15 · Alembic · Pytest · Ruff · MyPy strict · Docker

---

## The business problem

Overselling is one of the most common and most expensive failures in an online store. It
happens like this: two customers buy the last unit of the same product in the same second.
Both read the available stock, both see `stock = 1`, and both confirm. The database now
holds **two orders against one unit that never existed**.

| Problem | Real cost | What addresses it here |
| :--- | :--- | :--- |
| **Overselling through a race condition.** Two concurrent orders read the same stock before either writes | Orders that cannot be fulfilled: refund, cancellation, expedited shipping. On marketplaces like Amazon and eBay, repeated overselling is a direct cause of seller account suspension | Pessimistic row locking with `SELECT ... FOR UPDATE` per product: the second order **waits** for the first to commit, then reads the real stock |
| **Orders saved halfway.** If the third line of a ten-line order fails, a naive design leaves the first two already discounted | Inventory out of sync with what was charged. The customer paid for something the system no longer records | One transaction across all lines: the complete order is saved, or nothing is saved and stock stays intact |
| **Stock changing with no trail.** A manual adjustment, a data-entry error, a warehouse discrepancy: nothing explains why inventory says 12 | Reconciliation impossible, auditing impossible, no way to tell a data error from a real loss | Kardex: every stock change is recorded with quantity, reason, resulting stock, and the originating order where applicable |
| **Money in floating point.** `0.1 + 0.2` in floats is not `0.3` | Rounding errors that accumulate and end up as cash discrepancies and tax filing problems | `Decimal` with explicit `max_digits` and `decimal_places` on every monetary column |

---

## Use case: where this service fits

This is not a FastAPI tutorial. It is the **order and inventory core** of an online store:
the part that, when it is wrong, produces overselling and lost money. The same four
guarantees shown above are what separate a hobby from a system that can handle real money.

**Where a company would use it**

| Context | How it is used | Why it fits |
| :--- | :--- | :--- |
| **Own store with an online catalogue** | The frontend (Shopify, a custom build, a mobile app) calls this API to list products, create orders and check stock | The storefront does not need to know anything about concurrency: it places the order and the API guarantees there is no oversell |
| **Marketplace or platform with several sellers** | Each order carries its own stock line and kardex entry, which makes commission settlement and per-seller reconciliation possible | `StockMovement` doubles as an auditable ledger, per order |
| **Physical retail that also sells online** | Stock is shared: the physical store decrements through this API and the online channel sees the same number | One source of truth instead of two inventories that contradict each other |
| **Wholesale or B2B with per-customer pricing** | The category and customer structure allows segmentation without duplicating the catalogue | `Decimal` and `StockMovement` leave the trail an audit requires |

**What this adds over a FastAPI CRUD**

A FastAPI CRUD takes an afternoon. What is genuinely hard, and what this project implements, is
the part that shows up as a concurrency bug at 3am:

- **Row locking is the guarantee, not a detail.** `SELECT ... FOR UPDATE` per product is what
  makes the second buyer wait. Without it, two simultaneous requests read the same stock and
  both confirm.
- **One transaction for the whole order.** The classic bug — decrementing the first line and
  failing on the third — leaves inventory out of sync with what was charged.
- **The kardex answers "why is the stock 12?".** Without a movement log, that question has no
  answer and inventory shrinkage becomes invisible.

**What would be needed before production**

- **Authentication and authorisation.** The API is currently open. It needs JWT with roles,
  because in a real catalogue there is a difference between what a customer can see and what
  an administrator can see. The same design is already solved in
  [`ecommerce-inventory-automator`](https://github.com/jerryszc/ecommerce-inventory-automator).
- **Rate limiting** per IP and per customer, so that a script cannot drain the stock.
- **Observability**: metrics and traces, to detect degradation before customers do.
- **Cursor-based pagination** on long listings, and route versioning (`/api/v1`) before there
  are clients depending on the current shape.

**Which role this work maps to**

Backend Developer in e-commerce, logistics or retail tech. It is the kind of system that shows
up inside teams that own the outcome: the business depends on stock being correct, so the work
is measured by effects, not by endpoints.

---

## Verifiable impact

Everything below is backed by this repository's code and by specifically named tests. There
are no estimated business metrics: every guarantee has its proof.

| Guarantee | Test that proves it |
| :--- | :--- |
| A single-line order without enough stock leaves nothing behind | `test_order_insufficient_stock_single_line_rolls_back` |
| A multi-line order is **atomic**: if one line fails, none are applied | `test_order_multi_line_atomic_rollback` |
| An inactive product cannot be ordered and produces no side effects | `test_order_inactive_product_rejected_and_no_side_effects` |
| An adjustment exceeding stock is rejected (400) and leaves **no** orphan movement | `test_adjust_insufficient_stock_returns_400_and_no_movement` |
| A stock adjustment writes its kardex entry with the resulting stock | `test_adjust_in_increases_stock_and_kardex` |
| Duplicate SKU returns 409 | `test_duplicate_sku_returns_409` |
| Duplicate email returns 409 | `test_duplicate_email_returns_409` |
| Zero or negative order quantity returns 422 | `test_order_quantity_zero_returns_422`, `test_order_quantity_negative_returns_422` |
| Invalid pagination is rejected with 422 instead of dumping the whole table | `test_categories_invalid_pagination_422` |
| Price range filtering and pagination work on products | `test_products_price_range_and_pagination` |
| Order filtering by customer and status works | `test_orders_filter_by_customer_and_status` |

**34 tests** across 5 modules, with a **80% coverage gate** set in the Pytest configuration:
CI fails if coverage drops below that threshold.

---

## The transactional guarantee

This is the core of the project. It all happens in `app/services/order_service.py`:

```python
for product_id, quantity in lines:
    product = session.exec(
        select(Product).where(Product.id == product_id).with_for_update()
    ).one_or_none()

    if product.stock < quantity:
        raise ValueError(f"Insufficient stock for product {product_id}")

    product.stock -= quantity
    session.add(product)
    session.add(StockMovement(
        product_id=product.id,
        quantity_change=-quantity,
        quantity_after=product.stock,
        reason=MovementReason.OUT,
        order_id=order.id,
    ))
```

**What it does, in order:**

1. `with_for_update()` acquires a **row lock** in PostgreSQL. Any other transaction trying
   to read that same product **waits** until this one finishes. This is what removes
   overselling.
2. Available stock is validated. If it is not enough, the exception is raised **before**
   anything is written.
3. Stock is decremented and the kardex movement is recorded with the resulting stock.
4. `session.flush()` assigns `order.id` without committing, so lines and kardex entries can
   reference the order.

**Commit control belongs to the caller** (`app/api/deps.py`):

```python
def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

A single transaction wraps every line of the order. Any exception triggers `rollback()`,
and because the stock decrement happens inside that same transaction, inventory returns to
its previous state together with the order.

**Why pessimistic and not optimistic.** The optimistic pattern (retry when `version` changed)
suits systems where conflicts are rare. In an e-commerce checkout, conflicts on the same SKU
are **frequent** — a popular product concentrates most of the demand. Locking and
serialising is simpler to reason about and faster under that load, because retrying during a
traffic spike only moves the problem around.

---

## Data model

**6 tables.**

| Table | Key fields | Constraints |
| :--- | :--- | :--- |
| `category` | `name` (UNIQUE, index), `description` | `name` max 100 chars |
| `product` | `sku` (UNIQUE, index), `name` (index), `price` (Decimal), `stock`, `is_active`, `category_id` (FK) | `price` ≥ 0, 10 digits / 2 decimals · `stock` ≥ 0 |
| `customer` | `email` (UNIQUE, index), `full_name`, `address` | `email` max 255 chars |
| `order_` | `customer_id` (FK, index), `status` (enum), `total` (Decimal 12/2) | `created_at` and `updated_at` managed by the app |
| `order_item` | `order_id` (FK), `product_id` (FK), `quantity`, `unit_price` (Decimal 10/2) | `quantity` > 0 · `unit_price` ≥ 0 |
| `stock_movement` | `product_id` (FK), `quantity_change`, `quantity_after`, `reason` (enum), `order_id` (optional FK) | Kardex: `quantity_after` ≥ 0 |

**Relationships:** Category 1→N Product · Customer 1→N Order · Order 1→N OrderItem ·
Product 1→N OrderItem · Product 1→N StockMovement · Order 1→N StockMovement

**Design decisions**

- **`Decimal` for all money**, never `float`. `price`, `unit_price` and `total` declare
  `max_digits` and `decimal_places`.
- **Quantities validated in the model**, not only in the endpoint: `stock` with `ge=0`,
  `quantity` with `gt=0`. The database rejects impossible data even if someone writes
  straight to the API.
- **The kardex is a first-class table**, not a log. It is queryable and reconcilable.

---

## API

| Method | Path | Description | Success |
| :--- | :--- | :--- | :--- |
| GET | `/health` | Health probe | 200 |
| POST | `/categories` | Create category | 201 |
| GET | `/categories` | List with `?q=` and pagination | 200 |
| GET | `/categories/{id}` | Detail | 200 |
| POST | `/products` | Create product | 201 |
| GET | `/products` | List with `?q=`, `category_id`, `is_active`, `min_price`, `max_price`, pagination | 200 |
| GET | `/products/{id}` | Detail | 200 |
| POST | `/customers` | Create customer | 201 |
| GET | `/customers` | List with `?q=` and pagination | 200 |
| GET | `/customers/{id}` | Detail | 200 |
| POST | `/orders` | Create order (transactional) | 201 |
| GET | `/orders` | List with `?customer_id=`, `status=`, pagination | 200 |
| GET | `/orders/{id}` | Detail with lines | 200 |
| POST | `/inventory/adjust` | Adjust stock manually, writes kardex | 201 |
| GET | `/inventory/movements` | Query kardex with `?product_id=`, `reason=`, pagination | 200 |

**Interactive docs:** `/docs` (Swagger) and `/redoc`.

### Error strategy

Status codes are not arbitrary: each one distinguishes a cause the client must handle
differently.

| Code | When | Example |
| :--- | :--- | :--- |
| `201` | Resource created successfully | `POST /products` |
| `400` | Well-formed request that cannot be satisfied | Adjustment without enough stock, `quantity_change = 0`, missing product in an order |
| `404` | The resource does not exist | `GET /orders/999` |
| `409` | Conflict with current state: duplicate | Repeated SKU, repeated email, repeated category |
| `422` | Schema validation failed, before touching the database | `quantity = 0`, `lines = []`, negative `price`, out-of-range pagination |

`422` is produced natively by Pydantic from the model constraints
(`Field(gt=0)`, `Field(ge=0)`, `min_length=1`, `Query(ge=0, le=100)`), so a client receives
the offending field detail without any hand-written validation.

### Pagination

All lists use `skip` and `limit`, with validated bounds: `skip ≥ 0` and `1 ≤ limit ≤ 100`.
The 100 ceiling exists to stop a client from requesting the whole table in one request.

```bash
curl "http://localhost:8000/products?category_id=1&is_active=true&min_price=10&max_price=100&skip=0&limit=20"
```

---

## Tests

**34 tests** across 5 modules, organised by the guarantee they verify rather than by the
source file they exercise.

| Module | Tests | Covers |
| :--- | :--- | :--- |
| `test_orders.py` | 6 | Happy path, rollback for insufficient stock on single and multi-line orders, inactive product, missing product, 404 |
| `test_inventory.py` | 6 | Inbound and outbound adjustments, kardex, `quantity_change = 0` (400), insufficient stock (400) with no orphan movement, 404, product filter |
| `test_validation.py` | 9 | Zero quantity, negative quantity, empty lines, invalid `product_id`, missing fields, negative price and stock |
| `test_get_filters.py` | 9 | Search and pagination across all four entities, category, status, price range, customer, order status and movement reason filters, invalid pagination (422) |
| `test_duplicates.py` | 4 | Duplicate SKU, email and category (409), plus the valid case of same name with a different SKU |

```bash
# Full suite with coverage (the 80% gate applies automatically)
pytest

# See the coverage detail
pytest --cov=app --cov-report=term-missing

# Only the transactional tests, which are the heart of the project
pytest -k "order or stock"
```

`--cov-fail-under=80` lives in `addopts` in `pyproject.toml`, so the suite cannot be run
while bypassing the coverage control.

---

## Continuous integration

`.github/workflows/ci.yml` defines **4 jobs** running in parallel, plus a fifth that
notifies if any of them fail:

| Job | What it does |
| :--- | :--- |
| **Lint** | `ruff check .` and `ruff format --check .` |
| **Typecheck** | `mypy app` with `strict = true` |
| **Tests** | `pytest` with coverage and the 80% gate |
| **Docker Build & Smoke Test** | Builds the image, brings up the compose stack and checks `/health` with `curl -f`; on failure it dumps the container logs |
| **Notify on Failure** | Aggregator job with `needs: [lint, typecheck, test, docker]` |

The Docker smoke test is the part that carries the most value for a reviewer: the image
not only has to **build**, it has to **boot and respond** in a clean environment.

**Ruff configuration:** `line-length = 100`, `target-version = "py311"`, rule set
`E, W, F, I, N, UP, B, C4, T20`. Alembic migrations are exempt from import and format rules
because they are generated.

**MyPy configuration:** `strict = true` with `disallow_untyped_defs`,
`disallow_incomplete_defs`, `no_implicit_optional` and `warn_return_any`. Alembic migrations
are excluded from strict checking for being auto-generated.

---

## Quick start

**Requirements:** Docker Desktop running.

```bash
# 1. Clone and enter
git clone https://github.com/jerryszc/ecommerce-backend-api.git
cd ecommerce-backend-api

# 2. Configure the environment
cp .env.example .env

# 3. Bring up the API and PostgreSQL 15
docker compose up --build -d

# 4. Verify
curl http://localhost:8000/health
# {"status":"ok"}

# 5. Interactive docs
#    http://localhost:8000/docs
```

The database service has a `pg_isready` healthcheck and the API starts with
`depends_on: condition: service_healthy`, so migrations never run against a database that
is not yet accepting connections. The start command is:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Tear down**

```bash
docker compose down      # Keep the volume
docker compose down -v   # Also drop the volume
```

### Demo data

`app/seed.py` is **idempotent**: it can run repeatedly without duplicating data.

```bash
docker compose exec api python -m app.seed
```

Creates 3 categories, 4 products and 1 customer.

### Local development without Docker

```bash
python -m venv .venv && source .venv/bin/activate   # Git Bash on Windows
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic current
```

---

## Deployment

**Public instance running:**

```
https://ecommerce-backend-api-sh6c.onrender.com/health   ->  {"status":"ok"}
https://ecommerce-backend-api-sh6c.onrender.com/docs      ->  interactive OpenAPI
```

The API is deployed on Render with its own PostgreSQL database. To try it without installing
anything:

```bash
# Status
curl https://ecommerce-backend-api-sh6c.onrender.com/health

# Create an order and watch the stock drop (row locking in action)
curl -X POST https://ecommerce-backend-api-sh6c.onrender.com/categories \
  -H "Content-Type: application/json" \
  -d '{"name":"Audio"}'

curl -X POST https://ecommerce-backend-api-sh6c.onrender.com/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Headphones","sku":"HP-100","price":"79.99","stock":4,"category_id":1}'

curl -X POST https://ecommerce-backend-api-sh6c.onrender.com/customers \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Demo Buyer","email":"demo@example.com"}'

# 2 units: stock goes 4 -> 2 and a kardex entry is written
curl -X POST https://ecommerce-backend-api-sh6c.onrender.com/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"lines":[{"product_id":1,"quantity":2}]}'

# 999 units: 400 and the stock does NOT change. The guarantee, checked in production.
curl -i -X POST https://ecommerce-backend-api-sh6c.onrender.com/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"lines":[{"product_id":1,"quantity":999}]}'
```

### How it was deployed

`render.yaml` is a **Render Blueprint**: a web service on the Docker runtime plus a
PostgreSQL database, both on the free plan, with credentials injected automatically and
`healthCheckPath: /health`. The container's `start.sh` runs `alembic upgrade head` on every
boot, so migrations ship with the deployment.

One detail that only shows up on Linux: the `Dockerfile` normalises `start.sh` to LF during
the build. With Windows line endings the shebang becomes `#!/bin/sh\r` and the kernel looks
for an interpreter named `/bin/sh\r`, which does not exist. Windows hides this and CI does
too, because the smoke test uses `docker compose` with a different entrypoint.

**Note:** Render's free plan suspends the service after a few minutes of inactivity and wakes
it on the next request, so the first load can take 30 seconds or more. That is normal for the
free tier, not a deployment failure.

---

## Scope and limitations

Being explicit about what this project **does not** have matters as much as what it does:

- **There is no authentication or authorisation.** No JWT, no roles, no login. It is an
  open API by design, and anyone exposing it must put it behind an authenticating gateway.
  Role-based access control is implemented in
  [`ecommerce-inventory-automator`](https://github.com/jerryszc/ecommerce-inventory-automator).
- **No caching and no rate limiting.**
- **No observability** (structured logging, metrics, tracing). It is implemented in the
  inventory project.
- **SQLite is not supported.** The connection URL is built as
  `postgresql+psycopg2://` in `app/core/config.py`, with no per-environment alternative.
  This is deliberate: the row locks that make the transactional guarantee work are specific
  to PostgreSQL, so accepting SQLite would imply the concurrent behaviour is covered when it
  is not.

---

## Environment variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DB_HOST` | `db` | PostgreSQL host (`localhost` outside Docker) |
| `DB_PORT` | `5432` | Port |
| `DB_NAME` | `proyecto_1` | Database name |
| `DB_USER` | `postgres` | User |
| `DB_PASSWORD` | `postgres` | Password |

---

## License

MIT — free for commercial and educational use. See [LICENSE](LICENSE).
