from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.marketplace import Product, ProductReview
from app.models.order import Order
from app.models.user import User
from app.services.audit import record_audit_event
from app.schemas.marketplace import ProductCreate, ReviewCreate

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

def product_payload(product: Product, db: Session) -> dict:
    average = db.query(func.avg(ProductReview.rating)).filter(ProductReview.product_id == product.id).scalar()
    count = db.query(func.count(ProductReview.id)).filter(ProductReview.product_id == product.id).scalar() or 0
    return {"id": product.id, "vendor_id": product.vendor_id, "vendor_name": product.vendor.full_name,
            "name": product.name, "category": product.category, "description": product.description,
            "price": product.price, "stock_quantity": product.stock_quantity, "unit": product.unit,
            "created_at": product.created_at, "average_rating": round(float(average), 2) if average is not None else None,
            "review_count": count}

@router.get("/products")
def list_products(q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Product).order_by(Product.created_at.desc())
    if q: query = query.filter(Product.name.ilike(f"%{q.strip()}%"))
    return [product_payload(p, db) for p in query.limit(200).all()]

@router.post("/products", status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"vendor", "farmer", "gardener"}:
        raise HTTPException(status_code=403, detail="Farmer, gardener and vendor accounts can list products.")
    product = Product(vendor_id=user.id, **payload.model_dump())
    db.add(product); db.flush(); record_audit_event(db, user, "created", "marketplace-products", product.id); db.commit(); db.refresh(product)
    return product_payload(product, db)

@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id, Product.vendor_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or you do not own it.")
    if db.query(Order).filter(Order.product_id == product.id).first():
        raise HTTPException(status_code=409, detail="This listing has order history. Set its stock to zero instead of deleting it.")
    record_audit_event(db, user, "deleted", "marketplace-products", product.id)
    db.delete(product)
    db.commit()

@router.post("/products/{product_id}/reviews", status_code=201)
def add_review(product_id: int, payload: ReviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.get(Product, product_id): raise HTTPException(status_code=404, detail="Product not found.")
    if user.role == "vendor": raise HTTPException(status_code=403, detail="Vendor accounts cannot review products.")
    product = db.get(Product, product_id)
    if product and product.vendor_id == user.id:
        raise HTTPException(status_code=403, detail="You cannot review your own product listing.")
    review = ProductReview(product_id=product_id, reviewer_id=user.id, **payload.model_dump())
    db.add(review); db.flush(); record_audit_event(db, user, "created", "product-reviews", review.id, {"product_id": product_id, "rating": payload.rating}); db.commit(); db.refresh(review)
    return {"id": review.id, "product_id": review.product_id, "reviewer_id": review.reviewer_id,
            "rating": review.rating, "comment": review.comment, "created_at": review.created_at}
