from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.session import get_db
from app.api.deps import current_user
from app.models.user import User
from app.models.product import Product
from app.models.review import Review
from app.schemas import ProductIn, ProductOut

router = APIRouter(prefix="/products", tags=["Marketplace"])

def serialize_product(p: Product, db: Session):
    avg, count = db.query(func.avg(Review.rating), func.count(Review.id)).filter(Review.product_id == p.id).one()
    return {"id": p.id, "seller_id": p.seller_id, "title": p.title, "description": p.description,
            "listing_type": p.listing_type, "category": p.category, "price": p.price, "unit": p.unit,
            "stock": p.stock, "seller_name": p.seller.full_name, "seller_role": p.seller.role,
            "seller_location": p.seller.location, "average_rating": float(avg or 0), "review_count": count or 0}

@router.get("", response_model=list[ProductOut])
def list_products(listing_type: str | None = Query(default=None), category: str | None = None,
                  search: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Product).where(Product.is_active.is_(True), Product.stock > 0)
    if listing_type in ("produce", "supply"): stmt = stmt.where(Product.listing_type == listing_type)
    if category: stmt = stmt.where(Product.category.ilike(f"%{category}%"))
    if search: stmt = stmt.where(Product.title.ilike(f"%{search}%"))
    products = db.scalars(stmt.order_by(Product.created_at.desc())).all()
    return [serialize_product(p, db) for p in products]

@router.post("", response_model=ProductOut)
def create_product(payload: ProductIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if payload.listing_type == "produce" and user.role != "farmer":
        raise HTTPException(403, "Only farmers can list farm produce.")
    if payload.listing_type == "supply" and user.role != "vendor":
        raise HTTPException(403, "Only vendors can list agricultural supplies.")
    p = Product(seller_id=user.id, **payload.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return serialize_product(p, db)

@router.get("/mine", response_model=list[ProductOut])
def my_products(db: Session = Depends(get_db), user: User = Depends(current_user)):
    products = db.scalars(select(Product).where(Product.seller_id == user.id).order_by(Product.created_at.desc())).all()
    return [serialize_product(p, db) for p in products]

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = db.get(Product, product_id)
    if not p: raise HTTPException(404, "Product not found.")
    if p.seller_id != user.id: raise HTTPException(403, "You can only remove your own listing.")
    p.is_active = False; db.commit()
    return {"ok": True}
