"""Product model: catalog core with stock."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.order_item import OrderItem
    from app.models.stock_movement import StockMovement


class Product(SQLModel, table=True):
    """Sellable item. Stock is the cached current quantity."""

    __tablename__ = "product"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    sku: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(index=True, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(max_digits=10, decimal_places=2, ge=0)
    stock: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    category_id: int | None = Field(default=None, foreign_key="category.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    category: Optional["Category"] = Relationship(back_populates="products")
    movements: list["StockMovement"] = Relationship(back_populates="product")
    order_items: list["OrderItem"] = Relationship(back_populates="product")
