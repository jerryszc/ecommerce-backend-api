"""Customer endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models.customer import Customer

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(payload: Customer, session: Session = Depends(get_session)) -> Customer:
    """Create a customer. Email must be unique."""
    exists = session.exec(select(Customer).where(Customer.email == payload.email)).first()
    if exists:
        raise HTTPException(status_code=409, detail="Email already exists")
    customer = Customer(
        email=payload.email, full_name=payload.full_name, address=payload.address
    )
    session.add(customer)
    session.flush()
    session.refresh(customer)
    return customer


@router.get("", response_model=list[Customer])
def list_customers(session: Session = Depends(get_session)) -> list[Customer]:
    """List all customers."""
    return list(session.exec(select(Customer).order_by(Customer.email)).all())


@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: int, session: Session = Depends(get_session)) -> Customer:
    """Get a customer by id."""
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
