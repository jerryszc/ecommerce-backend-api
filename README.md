![CI](https://github.com/jerryszc/ecommerce-backend-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)

# E-Commerce Inventory & Order Backend

> **Executive Summary:** Transactional backend designed to eliminate consistency loss in concurrent inventories and guarantee atomicity in e-commerce order processing.

---

## The Business Problem

In conventional e-commerce platforms, two critical failures compromise financial operations:

1. **Inventory race conditions:** Multiple users purchasing the last unit of a product simultaneously, generating negative stock.
2. **Transactional inconsistencies:** Purchase orders failing mid-way through the payment/inventory flow, leaving databases with orphaned or outdated records.

---

## Engineering Solution Implemented

* **Transactional Shielding:** Explicit transaction control (`commit`/`rollback` + `SELECT ... FOR UPDATE` in `app/services/order_service.py`) to guarantee absolute atomicity in concurrent sales. No negative stock, no partial orders.
* **Fail-Fast Boundary Validation:** Strict schemas with `Pydantic` to reject anomalies before persistence, returning typed errors (`422 Unprocessable Entity` for validation, `409 Conflict` for duplicates).
* **Guaranteed Quality (QA):** Hardened architecture with a suite of **34 automated tests (`pytest`)** focused on critical flows and edge cases — atomic orders/rollback, inventory/kardex, validation, filters/pagination — ensuring zero regressions in production.

---

## Tech Stack & Business Justification

| Technology | Version | Technical Purpose | Business Value |
| :--- | :--- | :--- | :--- |
| **Python** | 3.10+ | Core language | Mature ecosystem, type hints, async support |
| **FastAPI** | 0.141.1 | Async, typed API development (`app/main.py`, `app/api/routers/`) | High performance, automatic OpenAPI docs, clear contracts |
| **SQLModel** | 0.0.42 | ORM + Pydantic integration (`app/models/`) | Single source of truth for DB models & API schemas |
| **SQLAlchemy** | 2.0.54 | Core ORM engine (`app/core/database.py`) | Mature relational persistence, connection pooling |
| **Pydantic / Pydantic-Settings** | 2.11.0 / 2.15.0 | Validation & config (`app/core/config.py`, `app/api/routers/`) | Eliminates logic bugs from malformed data; 12-factor config |
| **PostgreSQL** | 15 (prod) / SQLite (tests) | Relational persistence (`docker-compose.yml`) | ACID guarantees, referential integrity, `FOR UPDATE` locking |
| **psycopg2-binary** | 2.9.13 | PostgreSQL driver | Production-grade async-safe connectivity |
| **Alembic** | 1.20.0 | Database migrations (`app/alembic/`) | Version-controlled schema evolution |
| **Docker / Docker Compose** | Latest | Containerization (`Dockerfile`, `docker-compose.yml`) | Reproducible `api + postgres` environments, prod parity |
| **Pytest** | Latest | Automated testing (`tests/` + `pytest.ini`) | Safe deployments, lower maintenance costs |
| **Uvicorn** | 0.53.0 | ASGI server | High-performance async HTTP server |

---

## Architecture & Key Features

### Modular Layer Structure
```
app/
├── api/
│   ├── deps.py           # Shared dependencies (DB session with commit/rollback)
│   └── routers/          # REST endpoints (categories, products, customers, orders, inventory)
├── core/
│   ├── config.py         # Pydantic-Settings: 12-factor env config (.env)
│   ├── database.py       # SQLAlchemy engine + session factory (pool_pre_ping)
│   └── datetime.py       # Shared UTC helpers (naive UTC, no deprecated utcnow)
├── models/               # SQLModel table definitions (Category, Product, Customer, Order, OrderItem, StockMovement)
├── schemas/              # (Reserved for future Pydantic response models)
├── services/
│   └── order_service.py  # Atomic order creation with FOR UPDATE locking + kardex
├── main.py               # FastAPI entrypoint, router registration, health check
└── seed.py               # Idempotent demo data seeding
```

### Domain Model (ER Overview)
```
Category (1) ───< (M) Product (1) ───< (M) OrderItem >─── (M) Order >─── (M) Customer
                              │
                              └───< (M) StockMovement (kardex/audit trail)
```
* **Product:** Cached `stock` column + full `StockMovement` history for rebuild/audit.
* **Order:** Header with computed `total`; status enum (`PENDING`, `PAID`, `SHIPPED`, `CANCELLED`).
* **OrderItem:** Frozen `unit_price` at purchase time; cascade delete with order.
* **StockMovement:** `quantity_change` (+IN/-OUT), `quantity_after`, `reason` (IN, OUT, ADJUST, RESERVE, RELEASE), optional `order_id` link.

### Concurrency Control & Transactional Guarantees
* **Pessimistic Locking:** `SELECT ... FOR UPDATE` (`with_for_update()`) on `Product` rows during order creation and inventory adjustment (`app/services/order_service.py:38`, `app/api/routers/inventory.py:28`).
* **Explicit Transaction Boundary:** Request-scoped session via `get_session()` dependency (`app/api/deps.py`, `app/core/database.py`) — commits on success, rolls back on any exception, closes in `finally`.
* **Atomic Multi-Line Orders:** `create_order()` flushes order to get `id`, processes all lines under same transaction; any `ValueError` (insufficient stock, inactive product, not found) triggers full rollback — no partial orders, no phantom stock deductions.

### Validation & Error Handling Strategy
| Layer | Mechanism | HTTP Code | Example |
| :--- | :--- | :--- | :--- |
| **Input (Pydantic)** | `Field(gt=0)`, `ge=0`, `min_length=1`, `max_length`, `unique` constraints | `422 Unprocessable Entity` | Negative quantity, empty lines, price < 0 |
| **Business Rules** | Explicit checks in service/router (`if product.stock < qty`, `if not product.is_active`) | `400 Bad Request` | Insufficient stock, inactive product, not found |
| **Uniqueness** | DB `UNIQUE` indexes + pre-insert `SELECT` in routers | `409 Conflict` | Duplicate SKU, email, category name |
| **Not Found** | `session.get()` + explicit check | `404 Not Found` | Missing product, customer, order, category |

### Observability & Operations
* **Health Check:** `GET /health` → `{"status": "ok"}` (used by Docker `HEALTHCHECK` and Compose `depends_on: condition: service_healthy`).
* **Structured Logging:** SQLAlchemy `echo=False` (configurable), Alembic `INFO` level.
* **Container Security:** Non-root user (`appuser`), `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, pip cache disabled.

---

## Quick Start

### Prerequisites
* Docker 24+ with Compose v2 (recommended)
* Or: Python 3.10+, PostgreSQL 15+ (local)

---

### Option A: Docker Compose (Recommended — Prod Parity)

```bash
# 1. Clone and configure
git clone https://github.com/jerryszc/Ecommerce-backend-API.git
cd Ecommerce-backend-API
cp .env.example .env

# 2. Build and run (API + PostgreSQL 15)
docker compose up --build
```

**What starts:**
| Service | Image | Port | Details |
| :--- | :--- | :--- | :--- |
| `db` | `postgres:15-alpine` | `5432` | Volume `pgdata`, `pg_isready` healthcheck (5s interval, 10 retries) |
| `api` | Built from `Dockerfile` | `8000` | Waits for `db` healthy → `alembic upgrade head` → `uvicorn app.main:app --host 0.0.0.0 --port 8000` |

**Verify:**
* Health: `http://127.0.0.1:8000/health`
* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

**Seed demo data (idempotent: 3 categories, 4 products, 1 customer):**
```bash
docker compose exec api python -m app.seed
```

**Stop / Reset:**
```bash
docker compose down           # Stop containers, keep volume
docker compose down -v        # Stop and delete pgdata volume (full reset)
```

---

### Option B: Local Development (Fast Iteration / Native Pytest)

```bash
# 1. Prepare virtual environment
python -m venv venv
source venv/Scripts/activate      # Git Bash / Windows
# venv\Scripts\activate           # CMD / PowerShell
pip install -r requirements.txt

# 2. Configure environment (PostgreSQL local)
cp .env.example .env
# Edit .env with your local Postgres credentials:
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=proyecto_1
# DB_USER=postgres
# DB_PASSWORD=your_secure_password

# 3. Migrate and seed
alembic upgrade head
python -m app.seed

# 4. Run API with hot reload
uvicorn app.main:app --reload --port 8000

# 5. Run test suite (34 tests, SQLite in-memory)
pytest -v
# Expected: 34 passed — inventory concurrency, negative-stock prevention, transactional rollback, strict validation
```

---

## API Endpoints Reference

Base URL: `http://localhost:8000` (or your host)

### Health
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness/readiness probe |

### Categories (`/categories`)
| Method | Path | Description | Response |
| :--- | :--- | :--- | :--- |
| `POST` | `/categories` | Create category (unique name) | `201 Category` |
| `GET` | `/categories` | List with search (`q`), pagination (`skip`, `limit`) | `200 List[Category]` |
| `GET` | `/categories/{id}` | Get by ID | `200 Category` / `404` |

### Products (`/products`)
| Method | Path | Description | Response |
| :--- | :--- | :--- | :--- |
| `POST` | `/products` | Create product (unique SKU, `price≥0`, `stock≥0`) | `201 Product` |
| `GET` | `/products` | List with filters: `q` (sku/name), `category_id`, `is_active`, `min_price`, `max_price`, pagination | `200 List[Product]` |
| `GET` | `/products/{id}` | Get by ID | `200 Product` / `404` |

### Customers (`/customers`)
| Method | Path | Description | Response |
| :--- | :--- | :--- | :--- |
| `POST` | `/customers` | Create customer (unique email) | `201 Customer` |
| `GET` | `/customers` | List with search (`q` on email/name), pagination | `200 List[Customer]` |
| `GET` | `/customers/{id}` | Get by ID | `200 Customer` / `404` |

### Orders (`/orders`) — **Transactional Core**
| Method | Path | Description | Response |
| :--- | :--- | :--- | :--- |
| `POST` | `/orders` | Place order: atomic stock decrement + kardex (`OUT` movements). Payload: `{customer_id, lines: [{product_id, quantity}]}` | `201 Order` / `400` (insufficient stock, inactive, not found) / `422` (validation) |
| `GET` | `/orders` | List newest first; filters: `customer_id`, `status` (enum), pagination | `200 List[Order]` |
| `GET` | `/orders/{id}` | Get by ID (includes items via relationship) | `200 Order` / `404` |

### Inventory (`/inventory`) — Kardex / Stock Adjustments
| Method | Path | Description | Response |
| :--- | :--- | :--- | :--- |
| `POST` | `/inventory/adjust` | Adjust stock atomically with `FOR UPDATE` lock; creates `StockMovement`. Payload: `{product_id, quantity_change (+/-), reason (IN/OUT/ADJUST/RESERVE/RELEASE)}` | `201 StockMovement` / `400` (insufficient stock, qty=0) / `404` / `422` |
| `GET` | `/inventory/movements` | Kardex list newest first; filters: `product_id`, `reason`, pagination | `200 List[StockMovement]` |

---

## Testing Strategy

**Framework:** `pytest` + `TestClient` (Starlette) + SQLite in-memory (`StaticPool`) for total isolation.

**Coverage (34 tests):**
| Module | Focus |
| :--- | :--- |
| `test_orders.py` | Happy path (stock discount, total, kardex), single-line rollback, multi-line atomic rollback, inactive product, not found |
| `test_inventory.py` | IN/OUT adjustments, zero/negative guards, insufficient stock, not found, filter by product |
| `test_validation.py` | Pydantic 422s: zero/negative quantities, empty lines, missing fields, negative price/stock |
| `test_duplicates.py` | 409 conflicts: SKU, email, category name; same name different SKU allowed |
| `test_get_filters.py` | Search (`q`), all filter combos, pagination boundaries, 422 on invalid pagination params |

**Run:**
```bash
pytest -v            # Verbose
pytest -x            # Stop on first failure
pytest -k "order"    # Filter by keyword
```

---

## Database Migrations (Alembic)

```bash
# Generate new revision (autogenerate from models)
alembic revision --autogenerate -m "descriptive message"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1

# Show history
alembic history --verbose
```

*Config:* `alembic.ini` points to `app/alembic/`; `env.py` reads `settings.database_url` from `.env`.

---

## Environment Variables (`.env`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `proyecto_1` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | *required* | Database password |

> **Never commit `.env`** — use `.env.example` as template. `pydantic-settings` loads `.env` automatically.

---

## Project Structure

```
.
├── app/
│   ├── alembic/              # Migration scripts + env.py
│   ├── api/
│   │   ├── deps.py           # DB session dependency
│   │   └── routers/          # 5 REST routers
│   ├── core/                 # Config, DB engine, datetime helpers
│   ├── models/               # 6 SQLModel tables + enums
│   ├── schemas/              # Reserved for response models
│   ├── services/             # Business logic (order_service)
│   ├── main.py               # FastAPI app factory
│   └── seed.py               # Idempotent demo data
├── tests/                    # 34 pytest cases (AAA pattern)
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## License

MIT — Free for personal and commercial use.
