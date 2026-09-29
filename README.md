# E-Commerce Backend API — Inventory & Orders

**[English version →](README.en.md)**

API transaccional de e-commerce con control de concurrencia a nivel de fila, kardex de
inventario y garantía de atomicidad en la creación de pedidos.

[![CI](https://github.com/jerryszc/ecommerce-backend-api/actions/workflows/ci.yml/badge.svg)](https://github.com/jerryszc/ecommerce-backend-api/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688.svg)](https://fastapi.tiangolo.com/)
[![MyPy strict](https://img.shields.io/badge/mypy-strict%20%7C%20passed-brightgreen.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-34%20passing%20%7C%20coverage%20gate%2080%25-brightgreen.svg)](tests)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Stack:** Python 3.11 · FastAPI · SQLModel · SQLAlchemy · PostgreSQL 15 · Alembic · Pytest · Ruff · MyPy strict · Docker

---

## El problema empresarial

La sobreventa es uno de los fallos más comunes y más caros de una tienda online. Ocurre
así: dos clientes compran la última unidad del mismo producto en el mismo segundo. Ambos
leen el stock disponible, ambos ven `stock = 1`, y ambos confirman la compra. La base de
datos ahora tiene **dos pedidos sobre una unidad que no existía**.

| Problema | Costo real | Qué lo resuelve aquí |
| :--- | :--- | :--- |
| **Sobreventa por condición de carrera.** Dos pedidos concurrentes leen el mismo stock antes de que ninguno escriba | Pedidos que no se pueden surtir: reembolso, cancelación y envío urgente. En marketplaces como Amazon y eBay, la sobreventa reiterada es causa directa de suspensión de cuenta del vendedor | Bloqueo pesimista de fila con `SELECT ... FOR UPDATE` por producto: el segundo pedido **espera** a que el primero confirme, y entonces ve el stock real |
| **Pedidos que se guardan a medias.** Si la tercera línea de un pedido de diez falla, un diseño ingenuo deja las dos primeras descontadas del inventario | Inventario desincronizado respecto a lo cobrado. El cliente pagó por algo que el sistema ya no registra | Una sola transacción para todas las líneas: o se guarda el pedido completo, o no se guarda nada y el stock vuelve intacto |
| **Stock que cambia sin rastro.** Un ajuste manual, un error de carga, un faltante en bodega: nada explica por qué el inventario dice 12 | Imposible conciliar, imposible auditar, imposible distinguir un error de datos de una pérdida real | Kardex: cada movimiento de stock se registra con cantidad, motivo, stock resultante y, si aplica, el pedido que lo originó |
| **Dinero en coma flotante.** `0.1 + 0.2` en punto flotante no es `0.3` | Errores de redondeo que se acumulan y terminan en desacuerdos de caja y problemas con la declaración de impuestos | `Decimal` con `max_digits` y `decimal_places` explícitos en toda la columna monetaria |

---

## Contexto de uso: dónde encaja este servicio

Este repositorio no es un tutorial de FastAPI. Es el **núcleo de pedidos e inventario** de
una tienda online: la parte que, si está mal, produce sobreventa y dinero perdido. Las
mismas cuatro garantías que se ven arriba son las que separan un hobby de un sistema que
puede procesar dinero real.

**En qué empresa tendría sentido**

| Contexto | Cómo se usa | Por qué encaja aquí |
| :--- | :--- | :--- |
| **Tienda propia con catálogo online** | El frontend (Shopify, tienda a medida, app móvil) consume esta API para listar productos, crear pedidos y consultar stock | El frontend no necesita saber nada de concurrencia: pide el pedido y la API garantiza que no se sobrevenda |
| **Marketplace o plataforma con varios vendedores** | Cada pedido genera su asiento en el kardex, lo que permite liquidar comisiones y conciliar por vendedor | `StockMovement` funciona como libro mayor auditable, con una entrada por pedido |
| **Retail físico con venta online** | El stock es el mismo: la tienda física descuenta vía esta API y el online ve el mismo número | Una sola fuente de verdad en lugar de dos inventarios que se contradicen |
| **Mayorista o B2B con precios por cliente** | La estructura de categorías y clientes permite segmentar sin duplicar el catálogo | `Decimal` y `StockMovement` dejan el rastro que exige una auditoría fiscal |

**Qué aporta frente a un CRUD con FastAPI**

Un CRUD con FastAPI se escribe en una tarde. Lo que cuesta de verdad, y que es lo que este
proyecto implementa, es lo que aparece como un fallo de concurrencia a las 3 de la mañana:

- **El bloqueo de fila es la garantía, no un detalle.** `SELECT ... FOR UPDATE` por producto
  es lo que hace que el segundo comprador espere. Sin eso, dos peticiones simultáneas leen el
  mismo stock y las dos confirman.
- **Una sola transacción para todo el pedido.** El error clásico —descontar la primera línea y
  fallar en la tercera— deja el inventario desincronizado respecto a lo cobrado.
- **El kardex permite responder "¿por qué el stock es 12?".** Sin registro de movimientos, esa
  pregunta no tiene respuesta y la pérdida de inventario se vuelve invisible.

**Qué tendría que añadirse antes de ponerlo en producción**

- **Autenticación y autorización.** Hoy la API es abierta. Necesita JWT con roles, porque en
  un catálogo real hay diferencias entre lo que puede ver un cliente y lo que ve un
  administrador. El mismo diseño ya está resuelto en
  [`ecommerce-inventory-automator`](https://github.com/jerryszc/ecommerce-inventory-automator).
- **Rate limiting** por IP y por cliente, para que un script no pueda agotar el stock.
- **Observabilidad**: métricas y trazas, para detectar degradación antes de que llegue a los
  clientes.
- **Paginación por cursor** en los listados largos, y versionado de la ruta (`/api/v1`) antes
  de que haya clientes que dependan de la forma actual.

**A qué puesto corresponde este trabajo**

Backend Developer en e-commerce, logística o retail tech. Es el tipo de sistema que aparece
dentro de equipos que se hacen cargo del resultado: el negocio depende de que el stock sea
correcto, y por eso se mide el trabajo por efectos, no por endpoints.

---

## Impacto verificable

Todo lo que sigue está respaldado por el código de este repositorio y por tests con nombre
específico. No hay métricas de negocio estimadas: cada garantía tiene su prueba.

| Garantía | Test que la demuestra |
| :--- | :--- |
| Un pedido de una sola línea sin stock suficiente no deja nada a medias | `test_order_insufficient_stock_single_line_rolls_back` |
| Un pedido de varias líneas es **atómico**: si una línea falla, ninguna se aplica | `test_order_multi_line_atomic_rollback` |
| Un producto inactivo no se puede pedir y no produce efectos secundarios | `test_order_inactive_product_rejected_and_no_side_effects` |
| Un ajuste que excede el stock se rechaza (400) y **no** deja un movimiento huérfano | `test_adjust_insufficient_stock_returns_400_and_no_movement` |
| Un ajuste de stock escribe su entrada de kardex con el stock resultante | `test_adjust_in_increases_stock_and_kardex` |
| SKU duplicado devuelve 409 | `test_duplicate_sku_returns_409` |
| Email duplicado devuelve 409 | `test_duplicate_email_returns_409` |
| Cantidad cero o negativa en un pedido devuelve 422 | `test_order_quantity_zero_returns_422`, `test_order_quantity_negative_returns_422` |
| La paginación inválida se rechaza con 422 en vez de devolver la base entera | `test_categories_invalid_pagination_422` |
| El filtro por rango de precio y paginación funciona en productos | `test_products_price_range_and_pagination` |
| El filtro de órdenes por cliente y estado funciona | `test_orders_filter_by_customer_and_status` |

**34 tests** en 5 módulos, con un gate de cobertura del **80%** definido en la configuración
de Pytest: la CI falla si la cobertura baja de ese umbral.

---

## La garantía transaccional

Es la pieza central del proyecto. Todo ocurre en `app/services/order_service.py`:

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

**Qué hace, en orden:**

1. `with_for_update()` acquires a **bloqueo de fila** en PostgreSQL. Cualquier otra
   transacción que intente leer ese mismo producto **espera** hasta que esta termine.
   Esto es lo que elimina la sobreventa.
2. Se valida el stock disponible. Si no alcanza, se lanza la excepción **antes** de
   escribir nada.
3. Se descuenta el stock y se registra el movimiento de kardex con el stock resultante.
4. `session.flush()` asigna el `order.id` sin confirmar la transacción, de modo que las
   líneas y el kardex puedan referenciar al pedido.

**El control de commit es del llamador** (`app/api/deps.py`):

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

Una única transacción envuelve todas las líneas del pedido. Cualquier excepción dispara
`rollback()`, y como el descuento de stock ocurre dentro de esa misma transacción, el
inventario vuelve a su estado anterior junto con el pedido.

**Por qué pesimista y no optimista.** El patrón optimista (reintentar si el `version`
cambió) sirve para sistemas con conflictos raros. En un checkout de e-commerce los
conflictos sobre el mismo SKU son **frecuentes** — un producto popular concentra la
mayoría de las compras. Bloquear y serializar es más simple de razonar y más rápido en
esa carga, porque un reintento en un pico de tráfico solo mueve el problema.

---

## Modelo de datos

**6 tablas.**

| Tabla | Campos clave | Restricciones |
| :--- | :--- | :--- |
| `category` | `name` (UNIQUE, index), `description` | `name` máximo 100 caracteres |
| `product` | `sku` (UNIQUE, index), `name` (index), `price` (Decimal), `stock`, `is_active`, `category_id` (FK) | `price` ≥ 0 con 10 dígitos / 2 decimales · `stock` ≥ 0 |
| `customer` | `email` (UNIQUE, index), `full_name`, `address` | `email` máximo 255 caracteres |
| `order_` | `customer_id` (FK, index), `status` (enum), `total` (Decimal 12/2) | `created_at` y `updated_at` gestionados por la app |
| `order_item` | `order_id` (FK), `product_id` (FK), `quantity`, `unit_price` (Decimal 10/2) | `quantity` > 0 · `unit_price` ≥ 0 |
| `stock_movement` | `product_id` (FK), `quantity_change`, `quantity_after`, `reason` (enum), `order_id` (FK opcional) | Kardex: `quantity_after` ≥ 0 |

**Relaciones:** Category 1→N Product · Customer 1→N Order · Order 1→N OrderItem ·
Product 1→N OrderItem · Product 1→N StockMovement · Order 1→N StockMovement

**Decisiones de diseño**

- **`Decimal` para todo el dinero**, nunca `float`. `price`, `unit_price` y `total` declaran
  `max_digits` y `decimal_places`.
- **Cantidades validadas en el modelo**, no solo en el endpoint: `stock` con `ge=0`,
  `quantity` con `gt=0`. La base de datos rechaza datos imposibles aunque alguien escriba
  directamente contra la API.
- **Kardex como tabla de primera clase**, no como log. Es consultable y reconciliable.

---

## API

| Método | Ruta | Descripción | Éxito |
| :--- | :--- | :--- | :--- |
| GET | `/health` | Sonda de salud | 200 |
| POST | `/categories` | Crear categoría | 201 |
| GET | `/categories` | Listar con `?q=` y paginación | 200 |
| GET | `/categories/{id}` | Detalle | 200 |
| POST | `/products` | Crear producto | 201 |
| GET | `/products` | Listar con `?q=`, `category_id`, `is_active`, `min_price`, `max_price`, paginación | 200 |
| GET | `/products/{id}` | Detalle | 200 |
| POST | `/customers` | Crear cliente | 201 |
| GET | `/customers` | Listar con `?q=` y paginación | 200 |
| GET | `/customers/{id}` | Detalle | 200 |
| POST | `/orders` | Crear pedido (transaccional) | 201 |
| GET | `/orders` | Listar con `?customer_id=`, `status=`, paginación | 200 |
| GET | `/orders/{id}` | Detalle con líneas | 200 |
| POST | `/inventory/adjust` | Ajustar stock manualmente, genera kardex | 201 |
| GET | `/inventory/movements` | Consultar kardex con `?product_id=`, `reason=`, paginación | 200 |

**Documentación interactiva:** `/docs` (Swagger) y `/redoc`.

### Estrategia de errores

Los códigos no son arbitrarios: cada uno distingue una causa que el cliente debe tratar de
forma distinta.

| Código | Cuándo | Ejemplo |
| :--- | :--- | :--- |
| `201` | Recurso creado correctamente | `POST /products` |
| `400` | Petición válida en forma pero imposible de satisfacer | Ajuste sin stock suficiente, `quantity_change = 0`, producto inexistente en un pedido |
| `404` | El recurso no existe | `GET /orders/999` |
| `409` | Conflicto con el estado actual: duplicado | SKU repetido, email repetido, categoría repetida |
| `422` | Falla la validación de esquema, antes de tocar la base de datos | `quantity = 0`, `lines = []`, `price` negativo, paginación fuera de rango |

`422` lo produce Pydantic de forma nativa sobre las restricciones del modelo
(`Field(gt=0)`, `Field(ge=0)`, `min_length=1`, `Query(ge=0, le=100)`), así que un cliente
recibe el detalle del campo inválido sin que haga falta escribir una validación a mano.

### Paginación

Todas las listas usan `skip` y `limit`, con límites validados: `skip ≥ 0` y `1 ≤ limit ≤ 100`.
El techo del 100 existe para impedir que un cliente solicite la tabla completa en un solo
request.

```bash
curl "http://localhost:8000/products?category_id=1&is_active=true&min_price=10&max_price=100&skip=0&limit=20"
```

---

## Pruebas

**34 tests** en 5 módulos, organizados por la garantía que verifican y no por el archivo
del código que ejercitan.

| Módulo | Tests | Cubre |
| :--- | :--- | :--- |
| `test_orders.py` | 6 | Camino feliz, rollback por falta de stock en una y en varias líneas, producto inactivo, producto inexistente, 404 |
| `test_inventory.py` | 6 | Ajustes de entrada y salida, kardex, `quantity_change = 0` (400), stock insuficiente (400) sin movimiento huérfano, 404, filtro por producto |
| `test_validation.py` | 9 | Cantidad cero, negativa, líneas vacías, `product_id` inválido, campos faltantes, precio y stock negativos |
| `test_get_filters.py` | 9 | Búsqueda y paginación en las cuatro entidades, filtros de categoría, estado, rango de precio, cliente, estado de orden y motivo de movimiento, paginación inválida (422) |
| `test_duplicates.py` | 4 | SKU, email y categoría duplicados (409), y el caso válido de mismo nombre con SKU distinto |

```bash
# Suite completa con cobertura (el gate del 80% se aplica solo)
pytest

# Ver el detalle de cobertura
pytest --cov=app --cov-report=term-missing

# Solo las pruebas transaccionales, que son el corazón del proyecto
pytest -k "order or stock"
```

El `--cov-fail-under=80` está en `addopts` de `pyproject.toml`, así que no se puede
ejecutar la suite saltándose el control de cobertura.

---

## Integración continua

`.github/workflows/ci.yml` define **4 jobs** que se ejecutan en paralelo, más un quinto
que notifica si cualquiera falla:

| Job | Qué hace |
| :--- | :--- |
| **Lint** | `ruff check .` y `ruff format --check .` |
| **Typecheck** | `mypy app` en modo `strict = true` |
| **Tests** | `pytest` con cobertura y gate del 80% |
| **Docker Build & Smoke Test** | Construye la imagen, levanta el compose y verifica `/health` con `curl -f`; si falla, vuelca los logs del contenedor |
| **Notify on Failure** | Job aggregator con `needs: [lint, typecheck, test, docker]` |

El smoke test en Docker es la parte que más valor aporta a un reclutador: no basta con que
la imagen **construya**, tiene que **arrancar y responder** en un entorno limpio.

**Configuración de Ruff:** `line-length = 100`, `target-version = "py311"`, reglas
`E, W, F, I, N, UP, B, C4, T20`. Las migraciones de Alembic están excluidas de reglas de
importación y formato porque son generadas.

**Configuración de MyPy:** `strict = true` con `disallow_untyped_defs`,
`disallow_incomplete_defs`, `no_implicit_optional` y `warn_return_any`. Las migraciones de
Alembic están excluidas del chequeo estricto por ser autogeneradas.

---

## Puesta en marcha

**Requisitos:** Docker Desktop en ejecución.

```bash
# 1. Clonar y entrar
git clone https://github.com/jerryszc/ecommerce-backend-api.git
cd ecommerce-backend-api

# 2. Configurar el entorno
cp .env.example .env

# 3. Levantar la API y PostgreSQL 15
docker compose up --build -d

# 4. Verificar
curl http://localhost:8000/health
# {"status":"ok"}

# 5. Documentación interactiva
#    http://localhost:8000/docs
```

El servicio de base de datos tiene `healthcheck` con `pg_isready`, y la API arranca con
`depends_on: condition: service_healthy`, de modo que las migraciones nunca corren contra
una base de datos que aún no acepta conexiones. El comando de arranque es:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Detener el entorno**

```bash
docker compose down      # Conserva el volumen
docker compose down -v   # Elimina también el volumen
```

### Datos de demostración

`app/seed.py` es **idempotente**: se puede ejecutar varias veces sin duplicar datos.

```bash
docker compose exec api python -m app.seed
```

Crea 3 categorías, 4 productos y 1 cliente.

### Desarrollo local sin Docker

```bash
python -m venv .venv && source .venv/bin/activate   # Git Bash en Windows
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Migraciones

```bash
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
alembic current
```

---

## Despliegue

`render.yaml` es un **Render Blueprint** listo para usar: servicio web con runtime Docker
y una base de datos PostgreSQL, ambos en el plan gratuito, con las credenciales inyectadas
automáticamente desde la base de datos y `healthCheckPath: /health`.

```bash
# En el dashboard de Render: New -> Blueprint -> conectar este repositorio
```

**Nota:** el plan gratuito de Render suspende el servicio tras un periodo de inactividad y
lo despierta de nuevo en la siguiente petición, por lo que la primera carga puede tardar
varios segundos. Esta configuración está lista para desplegarse, pero no hay una instancia
pública activa mantenida en este momento.

---

## Alcance y limitaciones

Ser explícito sobre lo que **no** tiene este proyecto importa tanto como lo que sí:

- **No hay autenticación ni autorización.** No hay JWT, ni roles, ni login. Es una API
  abierta por diseño, y quien la exponga debe ponerla detrás de un gateway autenticado.
  La autorización por roles sí está implementada en
  [`ecommerce-inventory-automator`](https://github.com/jerryszc/ecommerce-inventory-automator).
- **No hay caché ni rate limiting.**
- **No hay observabilidad** (logs estructurados, métricas, tracing). Está implementada en
  el proyecto de inventario.
- **SQLite no está soportado.** La URL de conexión se construye como
  `postgresql+psycopg2://` en `app/core/config.py`, sin alternativa por entorno. Es
  deliberado: los bloqueos de fila que hacen funcionar la garantía transaccional son
  específicos de PostgreSQL, así que aceptar SQLite daría la impresión de que el
  comportamiento concurrente está cubierto cuando no lo está.

---

## Variables de entorno

| Variable | Por defecto | Descripción |
| :--- | :--- | :--- |
| `DB_HOST` | `db` | Host de PostgreSQL (`localhost` fuera de Docker) |
| `DB_PORT` | `5432` | Puerto |
| `DB_NAME` | `proyecto_1` | Nombre de la base de datos |
| `DB_USER` | `postgres` | Usuario |
| `DB_PASSWORD` | `postgres` | Contraseña |

---

## Licencia

MIT — uso libre comercial y educativo. Ver [LICENSE](LICENSE).
