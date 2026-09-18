"""Category endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models.category import Category

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(payload: Category, session: Session = Depends(get_session)) -> Category:
    """Create a category. Name must be unique."""
    exists = session.exec(select(Category).where(Category.name == payload.name)).first()
    if exists:
        raise HTTPException(status_code=409, detail="Category already exists")
    category = Category(name=payload.name, description=payload.description)
    session.add(category)
    session.flush()
    session.refresh(category)
    return category


@router.get("", response_model=list[Category])
def list_categories(
    session: Session = Depends(get_session),
    q: str | None = Query(default=None, description="Filter by name substring"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[Category]:
    """List categories with search and pagination."""
    statement = select(Category).order_by(Category.name)
    if q:
        statement = statement.where(Category.name.contains(q))
    statement = statement.offset(skip).limit(limit)
    return list(session.exec(statement).all())


@router.get("/{category_id}", response_model=Category)
def get_category(category_id: int, session: Session = Depends(get_session)) -> Category:
    """Get a category by id."""
    category = session.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category
