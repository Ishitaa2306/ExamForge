"""
Auth service — thin wrapper used by API layer for any additional auth logic.
"""
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.database.models import User


class AuthService:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User | None:
        user = AuthService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
