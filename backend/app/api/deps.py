from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer = HTTPBearer(auto_error=False)

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Please sign in.")
    subject = decode_access_token(credentials.credentials)
    if not subject:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    user = db.get(User, int(subject))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Account not available.")
    return user

def require_roles(*roles: str):
    def checker(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission for this action.")
        return user
    return checker
