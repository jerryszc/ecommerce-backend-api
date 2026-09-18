"""Order endpoints with atomic stock handling."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models.order import Order
from app.services.order_service import create_order

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderLine(BaseModel):
    """Single order line input."""

    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    """Order creation payload."""

    customer_id: int = Field(gt=0)
    lines: list[OrderLine] = Field(min_length=1)


@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
def place_order(payload: OrderCreate, session: Session = Depends(get_session)) -> Order:
    """Create an order discounting stock atomically."""
    try:
        order = create_order(
            session,
            payload.customer_id,
            [(line.product_id, line.quantity) for line in payload.lines],
        )
        session.flush()
        session.refresh(order)
        return order
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[Order])
def list_orders(session: Session = Depends(get_session)) -> list[Order]:
    """List all orders newest first."""
    return list(session.exec(select(Order).order_by(Order.id.desc())).all())


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: int, session: Session = Depends(get_session)) -> Order:
    """Get an order by id."""
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
