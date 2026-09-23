"""Product endpoints."""

from decimal import Decimal
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models.product import Product, ProductCreate

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, session: Session = Depends(get_session)) -> Product:
    """Create a product. SKU must be unique."""
    exists = session.exec(select(Product).where(Product.sku == payload.sku)).first()
    if exists:
        raise HTTPException(status_code=409, detail="SKU already exists")
    product = Product(
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        stock=payload.stock,
        is_active=payload.is_active,
        category_id=payload.category_id,
    )
    session.add(product)
    session.flush()
    session.refresh(product)
    return product


@router.get("", response_model=list[Product])
def list_products(
    session: Session = Depends(get_session),
    q: str | None = Query(default=None, description="Filter by sku or name substring"),
    category_id: int | None = Query(default=None, gt=0),
    is_active: bool | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[Product]:
    """List products with search, filters and pagination."""
    statement = select(Product).order_by(Product.name)
    if q:
        # cast: at class level SQLModel exposes Column descriptors, but mypy sees
        # the instance type (str); the cast recovers the queryable expression.
        statement = statement.where(
            (cast(Any, Product.sku).contains(q)) | (cast(Any, Product.name).contains(q))
        )
    if category_id is not None:
        statement = statement.where(Product.category_id == category_id)
    if is_active is not None:
        statement = statement.where(Product.is_active == is_active)
    if min_price is not None:
        statement = statement.where(Product.price >= min_price)
    if max_price is not None:
        statement = statement.where(Product.price <= max_price)
    statement = statement.offset(skip).limit(limit)
    return list(session.exec(statement).all())


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int, session: Session = Depends(get_session)) -> Product:
    """Get a product by id."""
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
