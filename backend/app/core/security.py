"""Password hashing and signed login tokens."""
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from app.core.config import settings

_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return _hasher.hash(password)

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return _hasher.verify(stored_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False

def create_token(user_id: int) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expiry}, settings.jwt_secret_key, algorithm="HS256")

def get_token_user_id(token: str) -> int | None:
    try:
        return int(jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        return None
