# E-Commerce Inventory & Order Backend

> **Executive Summary:** Transactional backend designed to eliminate consistency loss in concurrent inventories and guarantee atomicity in e-commerce order processing.

---

## 💼 The Business Problem
In conventional e-commerce platforms, two critical failures compromise financial operations:
1. **Inventory race conditions:** Multiple users purchasing the last unit of a product simultaneously, generating negative stock.
2. **Transactional inconsistencies:** Purchase orders failing mid-way through the payment/inventory flow, leaving databases with orphaned or outdated records.

---

## 🛠️ Engineering Solution Implemented
* **Transactional Shielding:** Explicit transaction control (`commit`/`rollback` + `SELECT ... FOR UPDATE` in `app/services/order_service.py`) to guarantee absolute atomicity in concurrent sales. No negative stock, no partial orders.
* **Fail-Fast Boundary Validation:** Strict schemas with `Pydantic` to reject anomalies before persistence, returning typed errors (`422 Unprocessable Entity` for validation, `409 Conflict` for duplicates).
* **Guaranteed Quality (QA):** Hardened architecture with a suite of **34 automated tests (`pytest`)** focused on critical flows and edge cases — atomic orders/rollback, inventory/kardex, validation, filters/pagination — ensuring zero regressions in production.

---

## 🏗️ Tech Stack & Business Justification
| Technology | Technical Purpose | Business Value |
| :--- | :--- | :--- |
| **FastAPI** | Async, typed API development (`app/main.py`, `app/api/routers/`) | High performance and clear contracts (OpenAPI) |
| **SQLModel / Pydantic** | ORM and strict type validation (`app/models/`, `app/core/config.py`) | Elimination of logic bugs from malformed data |
| **PostgreSQL / SQLite** | Relational persistence multi-environment (Postgres prod via `psycopg2`, SQLite in-memory for tests) | Guaranteed referential and transactional integrity |
| **Pytest** | Automated business testing (`tests/` + `pytest.ini`) | Safe deployments and lower maintenance costs |
| **Docker + Compose** | Reproducible `api + postgres:15` environment (`Dockerfile`, `docker-compose.yml`) | Zero-friction onboarding, prod parity |

---

## ⚙️ Run — Option A: Docker Compose (Recommended)

Prerequisites: Docker 24+ with Compose v2.

1. **Clone and configure:**
   ```bash
   git clone https://github.com/jerryszc/Ecommerce-backend-API.git
   cd Ecommerce-backend-API
   cp .env.example .env
   ```
   `docker-compose.yml` already overrides `DB_HOST=db` for the API container and maps `POSTGRES_DB/USER/PASSWORD` from `DB_NAME/DB_USER/DB_PASSWORD`. No code changes needed.

2. **Build and run (API + PostgreSQL 15):**
   ```bash
   docker compose up --build
   ```
   This starts:
   - `db` → `postgres:15-alpine` on `localhost:5432` with volume `pgdata` + `pg_isready` healthcheck
   - `api` → waits for `db` healthy, runs `alembic upgrade head`, then `uvicorn app.main:app --host 0.0.0.0 --port 8000`

3. **Verify:**
   - Health: `http://127.0.0.1:8000/health`
   - Docs: `http://127.0.0.1:8000/docs`
   - Endpoints: `/categories`, `/products`, `/customers`, `/orders`, `/inventory/adjust`, `/inventory/movements`

4. **Seed demo data (optional):**
   ```bash
   docker compose exec api python -m app.seed
   ```
   Idempotent: 3 categories, 4 products, 1 demo customer.

5. **Stop / reset:**
   ```bash
   docker compose down
   docker compose down -v  # also deletes pgdata volume
   ```

---

## 🛠️ Run — Option B: Local (Optional, without Docker)

Use for fast iteration or running `pytest` natively.

1. **Prepare venv:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Git Bash / Windows
   # venv\Scripts\activate  # CMD / PowerShell
   pip install -r requirements.txt
   ```

2. **Configure env (Postgres local):**
   ```bash
   cp .env.example .env
   ```
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=proyecto_1
   DB_USER=postgres
   DB_PASSWORD=your_secure_password
   ```
   URL is built in `app/core/config.py` as `postgresql+psycopg2://DB_USER:DB_PASSWORD@DB_HOST:DB_PORT/DB_NAME`.

3. **Migrate and seed:**
   ```bash
   alembic upgrade head
   python -m app.seed
   ```

4. **Run API:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Run tests:**
   ```bash
   pytest -v
   ```
   Expected: **34 passed** — inventory concurrency, negative-stock prevention, transactional rollback, strict validation.
