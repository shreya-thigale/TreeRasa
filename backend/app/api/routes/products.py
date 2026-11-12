from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.session import get_db
from app.api.deps import current_user
from app.models.user import User
from app.models.product import Product
from app.models.review import Review
from app.schemas import ProductIn, ProductOut, StockUpdateIn
from app.core.config import settings

router = APIRouter(prefix="/products", tags=["Marketplace"])
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

def serialize_product(p: Product, db: Session):
    avg, count = db.query(func.avg(Review.rating), func.count(Review.id)).filter(Review.product_id == p.id).one()
    return {"id": p.id, "seller_id": p.seller_id, "title": p.title, "description": p.description,
            "listing_type": p.listing_type, "category": p.category, "price": p.price, "unit": p.unit,
            "stock": p.stock, "seller_name": p.seller.full_name, "seller_role": p.seller.role,
            "seller_location": p.seller.location, "average_rating": float(avg or 0), "review_count": count or 0,
            "image_url": f"/api/products/{p.id}/image" if p.image_data else None}

def validate_listing_type(listing_type: str, user: User):
    if listing_type == "produce" and user.role != "farmer":
        raise HTTPException(403, "Only farmers can list farm produce.")
    if listing_type == "supply" and user.role != "vendor":
        raise HTTPException(403, "Only vendors can list agricultural supplies.")

@router.get("", response_model=list[ProductOut])
def list_products(
    listing_type: str | None = Query(default=None),
    category: str | None = None,
    search: str | None = None,
    sort_by: str = Query(default="newest"),
    min_price: float | None = None,
    max_price: float | None = None,
    db: Session = Depends(get_db)
):
    stmt = select(Product).where(Product.is_active.is_(True), Product.stock > 0)
    if listing_type in ("produce", "supply"): stmt = stmt.where(Product.listing_type == listing_type)
    if category: stmt = stmt.where(Product.category.ilike(f"%{category}%"))
    if search: stmt = stmt.where(Product.title.ilike(f"%{search}%"))
    if min_price is not None:
     stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
     stmt = stmt.where(Product.price <= max_price)
    if sort_by == "price_low":
     stmt = stmt.order_by(Product.price.asc())

    elif sort_by == "price_high":
     stmt = stmt.order_by(Product.price.desc())

    elif sort_by == "newest":
     stmt = stmt.order_by(Product.created_at.desc())

    else:
     stmt = stmt.order_by(Product.created_at.desc())

    products = db.scalars(stmt).all()
    return [serialize_product(p, db) for p in products]

@router.post("", response_model=ProductOut)
def create_product(payload: ProductIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    validate_listing_type(payload.listing_type, user)
    p = Product(seller_id=user.id, **payload.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return serialize_product(p, db)

@router.post("/with-image", response_model=ProductOut)
async def create_product_with_image(
    title: str = Form(...), description: str = Form(""), listing_type: str = Form(...),
    category: str = Form(...), price: float = Form(...), unit: str = Form("kg"),
    stock: int = Form(...), image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db), user: User = Depends(current_user)
):
    validate_listing_type(listing_type, user)
    image_bytes = None
    image_mime = None
    if image and image.filename:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(415, "Upload a JPG, PNG or WEBP image.")
        image_bytes = await image.read()
        if len(image_bytes) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"Image must be under {settings.max_upload_mb} MB.")
        image_mime = image.content_type
    p = Product(seller_id=user.id, title=title, description=description,
        listing_type=listing_type, category=category, price=price, unit=unit, stock=stock,
        image_data=image_bytes, image_mime=image_mime)
    db.add(p); db.commit(); db.refresh(p)
    return serialize_product(p, db)

@router.get("/{product_id}/image")
def product_image(product_id: int, db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p or not p.image_data:
        raise HTTPException(404, "Product image not found.")
    return Response(content=p.image_data, media_type=p.image_mime or "application/octet-stream",
                    headers={"Cache-Control": "public, max-age=3600"})

@router.get("/mine", response_model=list[ProductOut])
def my_products(db: Session = Depends(get_db), user: User = Depends(current_user)):
    products = db.scalars(select(Product).where(Product.seller_id == user.id, Product.is_active.is_(True)).order_by(Product.created_at.desc())).all()
    return [serialize_product(p, db) for p in products]

@router.patch("/{product_id}/stock")
def update_product_stock(product_id: int, payload: StockUpdateIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = db.get(Product, product_id)
    if not p or not p.is_active:
        raise HTTPException(404, "Listing not found.")
    if p.seller_id != user.id:
        raise HTTPException(403, "You can only update stock for your own listing.")
    p.stock = payload.stock
    db.commit()
    db.refresh(p)
    return {"ok": True, "product_id": p.id, "stock": p.stock}

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = db.get(Product, product_id)
    if not p: raise HTTPException(404, "Product not found.")
    if p.seller_id != user.id: raise HTTPException(403, "You can only remove your own listing.")
    p.is_active = False; db.commit()
    return {"ok": True}
