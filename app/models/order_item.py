"""OrderItem model: Many-to-Many bridge Order <-> Product."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.product import Product


class OrderItem(SQLModel, table=True):
    """Line item with price frozen at purchase time."""

    __tablename__ = "order_item"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order_.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(max_digits=10, decimal_places=2, ge=0)

    order: "Order" = Relationship(back_populates="items")
    product: "Product" = Relationship(back_populates="order_items")
