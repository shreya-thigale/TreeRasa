from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.session import get_db
from app.api.deps import current_user
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.scan import PlantScan

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(current_user)):
    scans = db.scalar(select(func.count(PlantScan.id)).where(PlantScan.user_id == user.id)) or 0
    incoming = db.scalar(select(func.count(Order.id)).where(Order.seller_id == user.id)) or 0
    outgoing = db.scalar(select(func.count(Order.id)).where(Order.buyer_id == user.id)) or 0
    sales = db.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.seller_id == user.id, Order.status == "delivered")) or 0
    products = db.scalar(select(func.count(Product.id)).where(Product.seller_id == user.id, Product.is_active.is_(True))) or 0
    return {"scans": scans, "incoming_orders": incoming, "outgoing_orders": outgoing,
            "completed_sales": float(sales), "active_listings": products, "role": user.role}
