"""Customer model: One-to-Many -> Order."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.core.datetime import utcnow

if TYPE_CHECKING:
    from app.models.order import Order


class Customer(SQLModel, table=True):
    """Buyer placing orders."""

    __tablename__ = "customer"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    full_name: str = Field(max_length=150)
    address: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

    orders: list["Order"] = Relationship(back_populates="customer")
