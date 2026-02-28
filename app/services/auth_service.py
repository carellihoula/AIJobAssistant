import secrets
import urllib
import uuid
from datetime import datetime, timedelta

import requests
from fastapi import HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_access_token,
    verify_password,
)
from app.models.user import User
from app.schemas.user import ChangePasswordSchema, ForgotPasswordSchema, ResetPasswordSchema
from app.services.email_service import send_email
from app.services.token_service import (
    cleanup_expired_tokens,
    get_user_active_sessions,
    get_valid_refresh_token,
    revoke_all_user_tokens,
    revoke_refresh_token,
    store_refresh_token,
)

def login_user(
    form_data: OAuth2PasswordRequestForm,
    device_id: str | None,
    device_name: str | None,
    db: Session,
    response: Response,
) -> dict:
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not activated")

    if not device_id:
        device_id = str(uuid.uuid4())

    access_token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=15)
    )
    refresh_token, expires = create_refresh_token({"sub": str(user.id)})

    store_refresh_token(
        db=db,
        user_id=user.id,
        token=refresh_token,
        expires_at=expires,
        device_id=device_id,
        device_name=device_name,
    )
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600

    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite="lax", max_age=max_age)
    response.set_cookie("device_id", device_id, httponly=True, secure=True, samesite="lax", max_age=365 * 24 * 3600)

    cleanup_expired_tokens(db)

    return {"access_token": access_token, "token_type": "bearer"}


def get_google_login_url() -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "access_type": "offline",
        "prompt": "consent",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)


def handle_google_callback(
    code: str,
    device_id: str | None,
    db: Session,
    response: Response,
) -> dict:
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    token_res = requests.post(token_url, data=data).json()

    id_token_str = token_res.get("id_token")
    if not id_token_str:
        raise HTTPException(status_code=400, detail="Google auth failed")

    try:
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = idinfo["email"]
    full_name = idinfo.get("name")
    google_id = idinfo["sub"]

    user = db.query(User).filter(User.email == email).first()

    if not user:
        random_pw = secrets.token_urlsafe(32)
        hashed_pw = get_password_hash(random_pw)
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            hashed_password=hashed_pw,
            google_id=google_id,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    elif not user.google_id:
        user.google_id = google_id
        db.commit()

    if not device_id:
        device_id = str(uuid.uuid4())

    access_token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=15)
    )
    refresh_token, expires = create_refresh_token({"sub": str(user.id)})

    store_refresh_token(
        db=db,
        user_id=user.id,
        token=refresh_token,
        expires_at=expires,
        device_id=device_id,
        device_name="Google OAuth",
    )

    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600

    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite="lax", max_age=max_age)
    response.set_cookie("device_id", device_id, httponly=True, secure=True, samesite="lax", max_age=365 * 24 * 3600)

    return {"access_token": access_token, "token_type": "bearer"}


def request_password_reset(payload: ForgotPasswordSchema, db: Session) -> dict:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return {"msg": "If an account exists, a reset email has been sent"}

    reset_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)

    user.reset_token = reset_token
    user.reset_token_expires = expires_at
    db.add(user)
    db.commit()

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    send_email(
        to=user.email,
        subject="Reset your password",
        body=f"Click here to reset your password: {reset_link}"
    )

    return {"msg": "If an account exists, a reset email has been sent"}


def reset_password_with_token(payload: ResetPasswordSchema, db: Session) -> dict:
    user = db.query(User).filter(User.reset_token == payload.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    if datetime.utcnow() > user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Token expired")

    user.hashed_password = get_password_hash(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None

    db.add(user)
    db.commit()

    return {"msg": "Password has been reset successfully"}


def change_user_password(payload: ChangePasswordSchema, current_user: User, db: Session) -> dict:
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    db.refresh(current_user)

    return {"msg": "Password changed successfully"}


def rotate_refresh_token(
    refresh_token: str | None,
    device_id: str | None,
    db: Session,
    response: Response,
) -> dict:
    if not refresh_token or not device_id:
        raise HTTPException(status_code=401, detail="Missing credentials")

    payload = verify_access_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token")

    db_token = get_valid_refresh_token(db, refresh_token)

    if not db_token:
        user_id = payload.get("sub")
        if user_id:
            revoke_all_user_tokens(db, user_id)
        raise HTTPException(status_code=401, detail="Token reuse detected - all sessions revoked")

    if str(db_token.device_id) != str(device_id):
        raise HTTPException(status_code=401, detail="Device mismatch")

    user_id = payload["sub"]

    revoke_refresh_token(db, refresh_token)

    new_access_token = create_access_token({"sub": str(user_id)})
    new_refresh_token, expires = create_refresh_token({"sub": str(user_id)})

    store_refresh_token(
        db=db,
        user_id=user_id,
        token=new_refresh_token,
        expires_at=expires,
        device_id=db_token.device_id,
        device_name=db_token.device_name,
    )

    response.set_cookie("refresh_token", new_refresh_token, httponly=True, secure=True, samesite="lax", max_age=30 * 24 * 3600)

    return {"access_token": new_access_token}


def logout_device(refresh_token: str | None, db: Session, response: Response) -> dict:
    if refresh_token:
        revoke_refresh_token(db, refresh_token)

    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


def logout_all_devices(current_user: User, db: Session, response: Response) -> dict:
    revoke_all_user_tokens(db, current_user.id)
    response.delete_cookie("refresh_token")
    return {"message": "Logged out from all devices"}


def list_user_sessions(current_user: User, db: Session) -> list:
    sessions = get_user_active_sessions(db, current_user.id)
    return [
        {
            "device_id": s.device_id,
            "device_name": s.device_name,
            "created_at": s.created_at,
            "last_used_at": s.last_used_at,
        }
        for s in sessions
    ]
