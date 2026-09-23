"""Category model: One-to-Many -> Product."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.core.datetime import utcnow

if TYPE_CHECKING:
    from app.models.product import Product


class Category(SQLModel, table=True):
    """Product grouping (e.g. Electronics, Books)."""

    __tablename__ = "category"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

    products: list["Product"] = Relationship(back_populates="category")
