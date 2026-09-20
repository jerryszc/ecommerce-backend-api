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

---

## ⚙️ Quick Install & Run Guide

1. **Clone and prepare environment:**
   ```bash
   git clone https://github.com/jerryszc/Ecommerce-backend-API.git
   cd Ecommerce-backend-API
   python -m venv venv
   source venv/Scripts/activate  # Git Bash / Windows
   # venv\Scripts\activate  # CMD / PowerShell
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` (never commit it). Real keys from this repo:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=proyecto_1
   DB_USER=postgres
   DB_PASSWORD=your_secure_password
   ```
   URL is built in `app/core/config.py` as:
   `postgresql+psycopg2://DB_USER:DB_PASSWORD@DB_HOST:DB_PORT/DB_NAME`

3. **Database and seed:**
   ```bash
   alembic upgrade head
   python -m app.seed
   ```
   Idempotent seed: 3 categories, 4 products, 1 demo customer.

4. **Run the API with Uvicorn:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - Health: `http://127.0.0.1:8000/health`
   - Docs: `http://127.0.0.1:8000/docs`
   - Endpoints: `/categories`, `/products`, `/customers`, `/orders`, `/inventory/adjust`, `/inventory/movements`

5. **Run the test suite:**
   ```bash
   pytest -v
   ```
   Expected: **34 passed** — covering inventory concurrency, negative-stock prevention, transactional rollback, and strict validation.
