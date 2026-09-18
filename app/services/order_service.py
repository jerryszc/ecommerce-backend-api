"""Order service: atomic stock discount + kardex entry."""

from decimal import Decimal

from sqlmodel import Session, select

from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.stock_movement import MovementReason, StockMovement


def create_order(
    session: Session, customer_id: int, lines: list[tuple[int, int]]
) -> Order:
    """Create an order discounting stock atomically.

    Args:
        session: Active SQLModel session (caller owns commit/rollback).
        customer_id: FK to customer.
        lines: List of (product_id, quantity).

    Returns:
        The persisted Order with total computed.

    Raises:
        ValueError: If stock is insufficient or product is missing/inactive.
    """
    order = Order(customer_id=customer_id, status=OrderStatus.PENDING)
    session.add(order)
    session.flush()  # assign order.id without committing

    total = Decimal("0.00")
    assert order.id is not None

    for product_id, quantity in lines:
        product = session.exec(
            select(Product).where(Product.id == product_id).with_for_update()
        ).one_or_none()
        if product is None:
            raise ValueError(f"Product {product_id} not found")
        if not product.is_active:
            raise ValueError(f"Product {product_id} is inactive")
        if product.stock < quantity:
            raise ValueError(f"Insufficient stock for product {product_id}")

        line_total = product.price * quantity
        total += line_total

        session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
            )
        )
        product.stock -= quantity
        session.add(product)
        session.add(
            StockMovement(
                product_id=product.id,
                quantity_change=-quantity,
                quantity_after=product.stock,
                reason=MovementReason.OUT,
                order_id=order.id,
            )
        )

    order.total = total
    session.add(order)
    session.flush()
    return order
