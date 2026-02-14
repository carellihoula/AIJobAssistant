import datetime
import secrets
import urllib
import uuid
from jose import jwt, JWTError
import requests
from app.core.auth import get_current_user
from app.core.security import create_access_token
from app.schemas.user import ChangePasswordSchema, ForgotPasswordSchema, ResetPasswordSchema
from app.services.email_service import send_email
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
# from app.core.auth import create_access_token
from app.db.session import get_db
from app.models.user import User
from passlib.context import CryptContext
from app.core.config import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy.orm import Session


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["auth"])

# ----------------------------------------------------------------------------------------------------------
# Login with email and password
# ----------------------------------------------------------------------------------------------------------

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=60)
    token = create_access_token({"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": token, "token_type": "bearer"}

# ----------------------------------------------------------------------------------------------------------
# Google login
# ----------------------------------------------------------------------------------------------------------

@router.get("/google/login")
def google_login():
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "access_type": "offline",
        "prompt": "consent",
    }

    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)

# ----------------------------------------------------------------------------------------------------------
# Callback endpoint for Google
# ----------------------------------------------------------------------------------------------------------

@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
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

    # Verify Google ID token (THE RIGHT WAY)
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
        # Generate a temporary long random password
        random_pw = secrets.token_urlsafe(32)
        hashed_pw = pwd_context.hash(random_pw)
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            hashed_password=hashed_pw,
            google_id=google_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # JWT
    access_token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

# ----------------------------------------------------------------------------------------------------------
# Endpoint pour demander un reset
# ----------------------------------------------------------------------------------------------------------

@router.post("/forgot_password")
def forgot_password(payload: ForgotPasswordSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Don't reveal whether the email exists or not
        return {"msg": "If an account exists, a reset email has been sent"}

    # Generate a temporary token
    reset_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Store the token and expiration in the DB (add reset_token and reset_token_expires fields to User)
    user.reset_token = reset_token
    user.reset_token_expires = expires_at
    db.add(user)
    db.commit()

    # Send email
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    send_email(
        to=user.email,
        subject="Reset your password",
        body=f"Click here to reset your password: {reset_link}"
    )

    return {"msg": "If an account exists, a reset email has been sent"}

# ----------------------------------------------------------------------------------------------------------
# Reset password endpoint
# ----------------------------------------------------------------------------------------------------------

@router.post("/reset_password")
def reset_password(payload: ResetPasswordSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == payload.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    if datetime.utcnow() > user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Token expired")

    # Update password
    user.hashed_password = pwd_context.hash(payload.new_password)

    # Remove token so it can't be reused
    user.reset_token = None
    user.reset_token_expires = None

    db.add(user)
    db.commit()

    return {"msg": "Password has been reset successfully"}

# ----------------------------------------------------------------------------------------------------------
# Change password endpoint
# ----------------------------------------------------------------------------------------------------------

@router.post("/change_password")
def change_password(payload: ChangePasswordSchema,db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify that the old password is correct
    if not pwd_context.verify(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    # Hash the new password and update
    current_user.hashed_password = pwd_context.hash(payload.new_password)
    db.commit()
    db.refresh(current_user)

    return {"msg": "Password changed successfully"}