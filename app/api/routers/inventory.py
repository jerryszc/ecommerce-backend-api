"""Inventory endpoints: stock adjustments and kardex."""

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models.product import Product
from app.models.stock_movement import MovementReason, StockMovement

router = APIRouter(prefix="/inventory", tags=["inventory"])


class StockAdjust(BaseModel):
    """Stock adjustment payload."""

    product_id: int = Field(gt=0)
    quantity_change: int = Field(description="+in / -out, 0 not allowed")
    reason: MovementReason = MovementReason.ADJUST


@router.post("/adjust", response_model=StockMovement, status_code=status.HTTP_201_CREATED)
def adjust_stock(payload: StockAdjust, session: Session = Depends(get_session)) -> StockMovement:
    """Adjust stock and record a kardex movement atomically."""
    if payload.quantity_change == 0:
        raise HTTPException(status_code=400, detail="quantity_change cannot be 0")
    product = session.exec(
        select(Product).where(Product.id == payload.product_id).with_for_update()
    ).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    new_stock = product.stock + payload.quantity_change
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    product.stock = new_stock
    session.add(product)
    movement = StockMovement(
        product_id=product.id,
        quantity_change=payload.quantity_change,
        quantity_after=new_stock,
        reason=payload.reason,
    )
    session.add(movement)
    session.flush()
    session.refresh(movement)
    return movement


@router.get("/movements", response_model=list[StockMovement])
def list_movements(
    session: Session = Depends(get_session),
    product_id: int | None = Query(default=None, gt=0),
    reason: MovementReason | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[StockMovement]:
    """List kardex movements newest first with filters and pagination."""
    # cast: StockMovement.id is Optional[int] at type level (SQLModel PK pattern);
    # persisted rows always carry an int, so .desc() is sound.
    statement = select(StockMovement).order_by(cast(Any, StockMovement.id).desc())
    if product_id is not None:
        statement = statement.where(StockMovement.product_id == product_id)
    if reason is not None:
        statement = statement.where(StockMovement.reason == reason)
    statement = statement.offset(skip).limit(limit)
    return list(session.exec(statement).all())
