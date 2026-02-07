import secrets
import urllib
import uuid

from jose import jwt, JWTError
import requests
from app.core.security import create_access_token
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from datetime import timedelta
# from app.core.auth import create_access_token
from app.db.session import SessionLocal
from app.models.user import User
from passlib.context import CryptContext
from app.core.config import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=60)
    token = create_access_token({"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": token, "token_type": "bearer"}

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

@router.get("/google/callback")
def google_callback(code: str):
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

    db = SessionLocal()
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