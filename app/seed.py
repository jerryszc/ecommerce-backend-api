"""Idempotent initial seed: categories, products, demo customer."""

from decimal import Decimal
from typing import Any

from sqlmodel import Session, select

import app.models  # noqa: F401  (register metadata)
from app.core.database import engine
from app.models.category import Category
from app.models.customer import Customer
from app.models.product import Product
from app.models.stock_movement import MovementReason, StockMovement

CATEGORIES = ["Electronica", "Hogar", "Libros"]

PRODUCTS: list[dict[str, Any]] = [
    {
        "sku": "ELEC-001",
        "name": "Laptop 14",
        "price": Decimal("3500.00"),
        "stock": 10,
        "category": "Electronica",
    },
    {
        "sku": "ELEC-002",
        "name": "Mouse inalambrico",
        "price": Decimal("120.00"),
        "stock": 50,
        "category": "Electronica",
    },
    {
        "sku": "HOG-001",
        "name": "Lampara LED",
        "price": Decimal("85.50"),
        "stock": 30,
        "category": "Hogar",
    },
    {
        "sku": "LIB-001",
        "name": "Python practico",
        "price": Decimal("60.00"),
        "stock": 20,
        "category": "Libros",
    },
]


def get_or_create_category(session: Session, name: str) -> Category:
    """Get category by name or create it."""
    category = session.exec(select(Category).where(Category.name == name)).first()
    if category is None:
        category = Category(name=name)
        session.add(category)
        session.flush()
        session.refresh(category)
    return category


def get_or_create_product(
    session: Session,
    sku: str,
    name: str,
    price: Decimal,
    stock: int,
    category_id: int,
) -> Product:
    """Get product by SKU or create it with an IN kardex entry."""
    product = session.exec(select(Product).where(Product.sku == sku)).first()
    if product is None:
        product = Product(sku=sku, name=name, price=price, stock=stock, category_id=category_id)
        session.add(product)
        session.flush()
        session.refresh(product)
        session.add(
            StockMovement(
                product_id=product.id,
                quantity_change=stock,
                quantity_after=stock,
                reason=MovementReason.IN,
            )
        )
        session.flush()
    return product


def get_or_create_customer(session: Session, email: str, full_name: str) -> Customer:
    """Get customer by email or create it."""
    customer = session.exec(select(Customer).where(Customer.email == email)).first()
    if customer is None:
        customer = Customer(email=email, full_name=full_name)
        session.add(customer)
        session.flush()
        session.refresh(customer)
    return customer


def run_seed() -> None:
    """Run idempotent seed inside one transaction."""
    with Session(engine) as session:
        categories = {name: get_or_create_category(session, name) for name in CATEGORIES}
        for item in PRODUCTS:
            category = categories[str(item["category"])]
            assert category.id is not None
            get_or_create_product(
                session,
                sku=str(item["sku"]),
                name=str(item["name"]),
                price=item["price"],
                stock=int(item["stock"]),
                category_id=category.id,
            )
        get_or_create_customer(session, "demo@tienda.com", "Cliente Demo")
        session.commit()


if __name__ == "__main__":
    run_seed()
