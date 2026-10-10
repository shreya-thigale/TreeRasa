"""Administrative user management. An administrator account is created by a local CLI command."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.audit import record_audit_event

router = APIRouter(prefix="/admin", tags=["Administration"])
ALLOWED_ROLES = {"farmer", "gardener", "vendor", "doctor", "plant_pathologist", "nursery_manager",
                 "agricultural_extension_officer", "forest_officer", "research_scientist", "delivery_partner", "agronomist", "student", "administrator"}

class UserUpdate(BaseModel):
    role: str = Field(pattern="^(farmer|gardener|vendor|doctor|plant_pathologist|nursery_manager|agricultural_extension_officer|forest_officer|research_scientist|delivery_partner|agronomist|student|administrator)$")
    is_active: bool


def require_admin(user: User) -> None:
    if user.role != "administrator":
        raise HTTPException(status_code=403, detail="Administrator permission is required.")


def user_payload(user: User) -> dict:
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role,
            "is_active": user.is_active, "created_at": user.created_at}

@router.get("/users")
def list_users(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_admin(user)
    return [user_payload(account) for account in db.query(User).order_by(User.created_at.desc()).limit(1000).all()]

@router.patch("/users/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_admin(user)
    account = db.get(User, user_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    if account.id == user.id and (payload.role != "administrator" or not payload.is_active):
        raise HTTPException(status_code=400, detail="You cannot remove your own administrator access or deactivate your own account.")
    account.role = payload.role
    account.is_active = payload.is_active
    record_audit_event(db, user, "updated", "user-management", account.id, {"target_email": account.email, "new_role": account.role, "is_active": account.is_active})
    db.commit(); db.refresh(account)
    return user_payload(account)
