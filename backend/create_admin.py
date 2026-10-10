"""Create the first TreeRasa administrator account from the terminal.

Run from backend/ after PostgreSQL is running and backend/.env has been configured:
    python create_admin.py
The password is prompted securely and is never written into this source file.
"""
from getpass import getpass
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app import models  # noqa: F401 - registers every table
from app.models.user import User
from app.core.security import hash_password


def main() -> None:
    Base.metadata.create_all(bind=engine)
    full_name = input("Administrator full name: ").strip()
    email = input("Administrator email: ").strip().lower()
    password = getpass("Administrator password (at least 8 characters): ")
    if len(full_name) < 2 or "@" not in email or len(password) < 8:
        raise SystemExit("Enter a name, a valid email and a password of at least 8 characters.")
    with SessionLocal() as db:  # type: Session
        if db.query(User).filter(User.email == email).first():
            raise SystemExit("That email already has an account. Ask an existing administrator to update its role.")
        account = User(full_name=full_name, email=email, password_hash=hash_password(password), role="administrator", is_active=True)
        db.add(account); db.commit()
        print(f"Administrator account created for {email}.")
        print("Sign in through the React app. Do not share the password or commit it to Git.")


if __name__ == "__main__":
    main()
