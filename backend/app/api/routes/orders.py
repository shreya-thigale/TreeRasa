"""Order creation and role-aware order tracking for the local marketplace workflow.

This is not a payment gateway. It records orders and inventory changes in PostgreSQL;
real payments, tax invoices and courier integrations need separate provider setup.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.marketplace import Product
from app.models.order import Order
from app.models.user import User
from app.services.audit import record_audit_event

router = APIRouter(prefix="/marketplace", tags=["Orders and delivery"])

class OrderInput(BaseModel):
    quantity: int = Field(ge=1, le=10000)
    delivery_address: str = Field(min_length=8, max_length=500)

class OrderUpdate(BaseModel):
    status: str | None = None
    delivery_partner_id: int | None = None


def order_payload(order: Order, db: Session) -> dict:
    product = db.get(Product, order.product_id)
    buyer = db.get(User, order.buyer_id)
    vendor = db.get(User, order.vendor_id)
    partner = db.get(User, order.delivery_partner_id) if order.delivery_partner_id else None
    return {
        "id": order.id, "product_id": order.product_id, "product_name": product.name if product else "Removed product",
        "buyer_id": order.buyer_id, "buyer_name": buyer.full_name if buyer else "Unknown buyer",
        "vendor_id": order.vendor_id, "vendor_name": vendor.full_name if vendor else "Unknown vendor",
        "delivery_partner_id": order.delivery_partner_id, "delivery_partner_name": partner.full_name if partner else None,
        "quantity": order.quantity, "unit_price": order.unit_price, "total": round(order.quantity * order.unit_price, 2),
        "status": order.status, "delivery_address": order.delivery_address,
        "created_at": order.created_at, "updated_at": order.updated_at,
        "payment_status": "not_integrated",
    }

@router.post("/products/{product_id}/orders", status_code=201)
def place_order(product_id: int, payload: OrderInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product listing not found.")
    if product.vendor_id == user.id:
        raise HTTPException(status_code=400, detail="You cannot order your own product listing.")
    if product.stock_quantity < payload.quantity:
        raise HTTPException(status_code=409, detail="There is not enough stock for that quantity.")
    product.stock_quantity -= payload.quantity
    order = Order(buyer_id=user.id, vendor_id=product.vendor_id, product_id=product.id,
        quantity=payload.quantity, unit_price=product.price, delivery_address=payload.delivery_address.strip())
    db.add(order); db.flush(); record_audit_event(db, user, "created", "marketplace-orders", order.id, {"product_id": product.id, "quantity": payload.quantity}); db.commit(); db.refresh(order)
    return order_payload(order, db)


@router.get("/delivery-partners")
def list_delivery_partners(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"vendor", "farmer", "gardener"}:
        raise HTTPException(status_code=403, detail="Only product sellers can view delivery-partner options.")
    partners = db.query(User).filter(User.role == "delivery_partner", User.is_active.is_(True)).order_by(User.full_name.asc()).limit(200).all()
    return [{"id": partner.id, "full_name": partner.full_name, "email": partner.email} for partner in partners]

@router.get("/orders")
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Order)
    if user.role in {"vendor", "farmer", "gardener"}:
        # Sellers can see sales, and also see orders they personally placed.
        query = query.filter(or_(Order.vendor_id == user.id, Order.buyer_id == user.id))
    elif user.role == "delivery_partner":
        query = query.filter(Order.delivery_partner_id == user.id)
    else:
        query = query.filter(Order.buyer_id == user.id)
    return [order_payload(order, db) for order in query.order_by(Order.created_at.desc()).limit(200).all()]

@router.patch("/orders/{order_id}")
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    if user.role in {"vendor", "farmer", "gardener"} and order.vendor_id == user.id:
        if payload.delivery_partner_id is not None:
            partner = db.get(User, payload.delivery_partner_id)
            if not partner or partner.role != "delivery_partner" or not partner.is_active:
                raise HTTPException(status_code=422, detail="Choose an active delivery-partner account.")
            order.delivery_partner_id = partner.id
        if payload.status is not None:
            if payload.status not in {"accepted", "packed", "cancelled"}:
                raise HTTPException(status_code=422, detail="Vendors can set accepted, packed or cancelled status.")
            if order.status in {"delivered", "cancelled"}:
                raise HTTPException(status_code=409, detail="This order is already closed.")
            if payload.status == "cancelled" and order.status != "cancelled":
                product = db.get(Product, order.product_id)
                if product:
                    product.stock_quantity += order.quantity
            order.status = payload.status
    elif user.role == "delivery_partner" and order.delivery_partner_id == user.id:
        if payload.status not in {"picked_up", "out_for_delivery", "delivered"}:
            raise HTTPException(status_code=422, detail="Delivery partners can set picked_up, out_for_delivery or delivered status.")
        if order.status == "cancelled":
            raise HTTPException(status_code=409, detail="A cancelled order cannot be delivered.")
        order.status = payload.status
    else:
        raise HTTPException(status_code=403, detail="You cannot update this order.")
    record_audit_event(db, user, "updated", "marketplace-orders", order.id, {"status": order.status})
    db.commit(); db.refresh(order)
    return order_payload(order, db)
