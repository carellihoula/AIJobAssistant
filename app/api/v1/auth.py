from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import ChangePasswordSchema, ForgotPasswordSchema, ResetPasswordSchema
from app.services.auth_service import (
    change_user_password,
    get_google_login_url,
    handle_google_callback,
    list_user_sessions,
    login_user,
    logout_all_devices,
    logout_device,
    request_password_reset,
    reset_password_with_token,
    rotate_refresh_token,
)
from fastapi import APIRouter, Cookie, Depends, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    device_id: str | None = Cookie(default=None),
    device_name: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    return login_user(form_data, device_id, device_name, db, response)


@router.get("/google/login")
def google_login():
    return RedirectResponse(get_google_login_url())


@router.get("/google/callback")
def google_callback(
    code: str,
    response: Response,
    db: Session = Depends(get_db),
    device_id: str | None = Cookie(default=None),
):
    return handle_google_callback(code, device_id, db, response)


@router.post("/forgot_password")
def forgot_password(payload: ForgotPasswordSchema, db: Session = Depends(get_db)):
    return request_password_reset(payload, db)


@router.post("/reset_password")
def reset_password(payload: ResetPasswordSchema, db: Session = Depends(get_db)):
    return reset_password_with_token(payload, db)


@router.post("/change_password")
def change_password(
    payload: ChangePasswordSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return change_user_password(payload, current_user, db)


@router.post("/refresh")
def refresh_token_endpoint(
    response: Response,
    refresh_token: str = Cookie(default=None),
    device_id: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    return rotate_refresh_token(refresh_token, device_id, db, response)


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    return logout_device(refresh_token, db, response)


@router.post("/logout/all")
def logout_all(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return logout_all_devices(current_user, db, response)


@router.get("/sessions")
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_user_sessions(current_user, db)