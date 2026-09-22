"""StockMovement model: inventory kardex / audit trail."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum
from sqlmodel import Column, Field, Relationship, SQLModel

from app.core.datetime import utcnow

if TYPE_CHECKING:
    from app.models.product import Product


class MovementReason(StrEnum):
    """Reason for a stock change."""

    IN = "IN"
    OUT = "OUT"
    ADJUST = "ADJUST"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"


class StockMovement(SQLModel, table=True):
    """One row per stock change. Allows rebuilding Product.stock."""

    __tablename__ = "stock_movement"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    quantity_change: int = Field(description="+in / -out")
    quantity_after: int = Field(ge=0)
    reason: MovementReason = Field(
        default=MovementReason.ADJUST,
        sa_column=Column(
            SAEnum(
                MovementReason,
                values_callable=lambda e: [m.value for m in e],
                name="movementreason",
            ),
            nullable=False,
        ),
    )
    order_id: int | None = Field(default=None, foreign_key="order_.id")
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

    product: Optional["Product"] = Relationship(back_populates="movements")
