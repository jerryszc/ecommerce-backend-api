"""Order model: header of a purchase."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Column, Field, Relationship, SQLModel
from sqlalchemy import Enum as SAEnum

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.order_item import OrderItem


class OrderStatus(str, Enum):
    """Order lifecycle states."""

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class Order(SQLModel, table=True):
    """Customer purchase. Total is computed from its items."""

    __tablename__ = "order_"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        sa_column=Column(
            SAEnum(
                OrderStatus,
                values_callable=lambda e: [m.value for m in e],
                name="orderstatus",
            ),
            nullable=False,
        ),
    )
    total: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    customer: "Customer" = Relationship(back_populates="orders")
    items: list["OrderItem"] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
