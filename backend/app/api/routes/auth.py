from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.schemas import RegisterIn, LoginIn, TokenOut, UserOut
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists.")
    user = User(full_name=payload.full_name, email=email, password_hash=hash_password(payload.password),
                role=payload.role, phone=payload.phone, location=payload.location, farm_name=payload.farm_name)
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_access_token(str(user.id)), "user": user}

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(403, "This account is disabled.")
    return {"access_token": create_access_token(str(user.id)), "user": user}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
