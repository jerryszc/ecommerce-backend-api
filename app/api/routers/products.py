"""Product endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models.product import Product

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(payload: Product, session: Session = Depends(get_session)) -> Product:
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
def list_products(session: Session = Depends(get_session)) -> list[Product]:
    """List all products."""
    return list(session.exec(select(Product).order_by(Product.name)).all())


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int, session: Session = Depends(get_session)) -> Product:
    """Get a product by id."""
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
