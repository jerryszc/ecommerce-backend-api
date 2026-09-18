"""Import all models so SQLModel.metadata is complete for Alembic."""

from app.models.category import Category  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.order_item import OrderItem  # noqa: F401
from app.models.product import Product, ProductBase, ProductCreate  # noqa: F401
from app.models.stock_movement import MovementReason, StockMovement  # noqa: F401
from app.models.order import OrderStatus  # noqa: F401
