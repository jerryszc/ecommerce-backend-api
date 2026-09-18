"""Order endpoints with atomic stock handling."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models.order import Order, OrderStatus
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
def list_orders(
    session: Session = Depends(get_session),
    customer_id: int | None = Query(default=None, gt=0),
    status: OrderStatus | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[Order]:
    """List orders newest first with filters and pagination."""
    statement = select(Order).order_by(Order.id.desc())
    if customer_id is not None:
        statement = statement.where(Order.customer_id == customer_id)
    if status is not None:
        statement = statement.where(Order.status == status)
    statement = statement.offset(skip).limit(limit)
    return list(session.exec(statement).all())


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: int, session: Session = Depends(get_session)) -> Order:
    """Get an order by id."""
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
