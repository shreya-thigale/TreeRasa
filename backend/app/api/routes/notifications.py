from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.api.deps import current_user
from app.models.user import User
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

def notification_out(n):
    return {"id": n.id, "title": n.title, "message": n.message, "kind": n.kind,
            "is_read": n.is_read, "created_at": n.created_at.isoformat()}

@router.get("/mine")
def my_notifications(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id)
                      .order_by(Notification.created_at.desc()).limit(50)).all()
    return [notification_out(n) for n in rows]

@router.patch("/read-all")
def read_all(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))).all()
    for row in rows: row.is_read = True
    db.commit()
    return {"ok": True, "updated": len(rows)}

@router.patch("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    row = db.get(Notification, notification_id)
    if not row or row.user_id != user.id: raise HTTPException(404, "Notification not found.")
    row.is_read = True
    db.commit()
    return {"ok": True}
