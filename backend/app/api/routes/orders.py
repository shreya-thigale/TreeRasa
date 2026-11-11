from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.db.session import get_db
from app.api.deps import current_user
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.schemas import CheckoutIn, OrderStatusIn, ReviewIn
from app.models.review import Review
from app.models.notification import Notification

router = APIRouter(prefix="/orders", tags=["Orders"])

def order_out(o: Order, viewer_id: int, reviewed_item_ids: set[int] | None = None):
    buyer = o.buyer
    seller = o.seller
    return {"id": o.id, "order_number": o.order_number, "buyer_id": o.buyer_id, "seller_id": o.seller_id,
            "status": o.status, "total_amount": o.total_amount, "shipping_address": o.shipping_address,
            "created_at": o.created_at.isoformat(), "buyer": {"id": buyer.id, "full_name": buyer.full_name,
            "email": buyer.email, "phone": buyer.phone, "location": buyer.location} if o.seller_id == viewer_id else None,
            "seller": {"id": seller.id, "full_name": seller.full_name, "role": seller.role,
            "email": seller.email, "phone": seller.phone, "location": seller.location} if o.buyer_id == viewer_id else None,
            "items": [{"id": i.id, "product_id": i.product_id, "product_title": i.product_title,
                       "quantity": i.quantity, "unit_price": i.unit_price, "reviewed": i.id in (reviewed_item_ids or set())} for i in o.items]}

@router.post("/checkout")
def checkout(payload: CheckoutIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    product_ids = list({item.product_id for item in payload.items})
    products = db.scalars(select(Product).where(Product.id.in_(product_ids), Product.is_active.is_(True)).with_for_update()).all()
    by_id = {p.id: p for p in products}
    if len(by_id) != len(product_ids): raise HTTPException(404, "One or more products are unavailable.")
    quantities = {}
    for item in payload.items: quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
    for pid, qty in quantities.items():
        p = by_id[pid]
        if p.seller_id == user.id: raise HTTPException(400, "You cannot purchase your own listing.")
        if p.stock < qty: raise HTTPException(409, f"Not enough stock for {p.title}.")
    grouped = {}
    for pid, qty in quantities.items(): grouped.setdefault(by_id[pid].seller_id, []).append((by_id[pid], qty))
    created = []
    for seller_id, entries in grouped.items():
        total = sum(p.price * qty for p, qty in entries)
        order = Order(order_number="TR-" + uuid4().hex[:10].upper(), buyer_id=user.id, seller_id=seller_id,
                      status="placed", total_amount=total, shipping_address=payload.shipping_address)
        db.add(order); db.flush()
        for p, qty in entries:
            p.stock -= qty
            db.add(OrderItem(order_id=order.id, product_id=p.id, product_title=p.title, quantity=qty, unit_price=p.price))
        created.append(order)
        product_names = ', '.join(p.title for p, _ in entries)
        db.add(Notification(user_id=seller_id, title='New order received', message=f'{user.full_name} placed an order for {product_names}.', kind='order'))
        db.add(Notification(user_id=user.id, title='Order placed successfully', message=f'Your order {order.order_number} has been placed.', kind='order'))
    db.commit()
    return {"orders": [{"id": o.id, "order_number": o.order_number, "seller_id": o.seller_id,
                        "status": o.status, "total_amount": o.total_amount} for o in created]}

@router.get("/mine")
def my_orders(db: Session = Depends(get_db), user: User = Depends(current_user)):
    orders = db.scalars(select(Order).options(joinedload(Order.items), joinedload(Order.buyer), joinedload(Order.seller))
                        .where((Order.buyer_id == user.id) | (Order.seller_id == user.id))
                        .order_by(Order.created_at.desc())).unique().all()
    reviewed_item_ids = set(db.scalars(select(Review.order_item_id).where(Review.user_id == user.id)).all())
    return [order_out(o, user.id, reviewed_item_ids) for o in orders]

@router.patch("/{order_id}/status")
def update_status(order_id: int, payload: OrderStatusIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    order = db.get(Order, order_id)
    if not order: raise HTTPException(404, "Order not found.")
    if order.seller_id != user.id: raise HTTPException(403, "Only the seller can update this order.")
    if order.status in ("delivered", "cancelled"): raise HTTPException(409, "This order is already closed.")
    if payload.status == "cancelled":
        # Restore inventory for cancellation before delivery.
        items = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        for item in items:
            product = db.get(Product, item.product_id)
            if product: product.stock += item.quantity
    order.status = payload.status
    db.add(Notification(user_id=order.buyer_id, title='Order status updated', message=f'Your order {order.order_number} is now {payload.status}.', kind='order'))
    db.commit()
    return {"ok": True, "status": order.status}

@router.get("/reviews/product/{product_id}")
def product_reviews(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found.")
    rows = db.execute(
        select(Review, User.full_name)
        .join(User, User.id == Review.user_id)
        .where(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
    ).all()
    return [{
        "id": review.id,
        "rating": review.rating,
        "comment": review.comment,
        "reviewer_name": reviewer_name,
        "created_at": review.created_at.isoformat()
    } for review, reviewer_name in rows]

@router.post("/reviews")
def create_review(payload: ReviewIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.get(OrderItem, payload.order_item_id)
    if not item: raise HTTPException(404, "Order item not found.")
    order = db.get(Order, item.order_id)
    if order.buyer_id != user.id: raise HTTPException(403, "Only the buyer can review this item.")
    if order.status != "delivered": raise HTTPException(400, "You can review products after delivery.")
    if db.scalar(select(Review).where(Review.order_item_id == item.id)) or db.scalar(select(Review).where(Review.user_id == user.id, Review.product_id == item.product_id)):
        raise HTTPException(409, "You have already reviewed this product.")
    review = Review(user_id=user.id, product_id=item.product_id, order_item_id=item.id, rating=payload.rating, comment=payload.comment)
    db.add(review)
    db.add(Notification(user_id=order.seller_id, title='New product review', message=f'{user.full_name} rated {item.product_title} {payload.rating}/5.', kind='review'))
    db.commit()
    return {"ok": True, "message": "Review saved."}
