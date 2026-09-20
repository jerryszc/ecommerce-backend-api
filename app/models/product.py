"""Product model: catalog core with stock."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.core.datetime import utcnow

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.order_item import OrderItem
    from app.models.stock_movement import StockMovement


class ProductBase(SQLModel):
    """Shared fields with strict validation (non-table, enforced by Pydantic)."""

    sku: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(index=True, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(max_digits=10, decimal_places=2, ge=0)
    stock: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    category_id: int | None = Field(default=None, foreign_key="category.id", index=True)


class Product(ProductBase, table=True):
    """Sellable item. Stock is the cached current quantity."""

    __tablename__ = "product"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)

    category: Optional["Category"] = Relationship(back_populates="products")
    movements: list["StockMovement"] = Relationship(back_populates="product")
    order_items: list["OrderItem"] = Relationship(back_populates="product")


class ProductCreate(ProductBase):
    """API input schema. Pydantic enforces ge=0 -> FastAPI returns 422."""

    pass
