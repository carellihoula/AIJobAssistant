from uuid import UUID
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.core.config import settings
from app.services.email_service import send_email


def register_user(user: UserCreate, db: Session) -> User:
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    activation_token = str(uuid.uuid4())
    new_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=False,
        is_verified=False,
        reset_token=activation_token,
        reset_token_expires=datetime.utcnow() + timedelta(hours=24),
    )

    activation_link = f"{settings.FRONTEND_URL}/activate?token={activation_token}"
    send_email(
        to=user.email,
        subject="Activate your account",
        body=f"Click here to activate your account: {activation_link}"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def activate_user(token: str, db: Session) -> dict:
    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Token invalide")

    if datetime.utcnow() > user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Token expiré")

    user.is_active = True
    user.is_verified = True
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Your account has been activated successfully."}


def get_user_by_id(user_id: UUID, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
