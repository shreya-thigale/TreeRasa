from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterInput, LoginInput
from app.core.security import hash_password, verify_password, create_token
from app.api.dependencies import get_current_user
from app.services.audit import record_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])

def user_payload(user: User) -> dict:
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}

@router.post("/register", status_code=201)
def register(payload: RegisterInput, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(full_name=payload.full_name.strip(), email=email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user); db.flush(); record_audit_event(db, user, "registered", "authentication"); db.commit(); db.refresh(user)
    return {"access_token": create_token(user.id), "token_type": "bearer", "user": user_payload(user)}

@router.post("/login")
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is currently inactive.")
    record_audit_event(db, user, "signed_in", "authentication")
    db.commit()
    return {"access_token": create_token(user.id), "token_type": "bearer", "user": user_payload(user)}

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_payload(user)
