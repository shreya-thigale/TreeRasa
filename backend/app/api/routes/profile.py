from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import current_user
from app.models.user import User
from app.schemas import ProfileIn, UserOut

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.patch("", response_model=UserOut)
def update_profile(payload: ProfileIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    for key, value in payload.model_dump().items():
        setattr(user, key, value)
    db.commit(); db.refresh(user)
    return user
