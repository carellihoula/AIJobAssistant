from sqlalchemy.orm import Session
from datetime import datetime
from app.models.refresh_token import RefreshToken
from app.core.security import hash_token
from app.db.session import get_db
from fastapi import Depends


def store_refresh_token(
    db: Session,
    user_id,
    token: str,
    expires_at,
    device_id: str,
    device_name: str = None,
):
    # Delete old token if exists
    old_token = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.device_id == device_id,
    ).first()

    if old_token:
        db.delete(old_token)
        db.flush()                    # flush before insert to avoid unique conflict

    db_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(token),
        device_id=device_id,
        device_name=device_name,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()
    return db_token

# Validate a refresh token and return the corresponding database record
def get_valid_refresh_token(db: Session, token: str):
    token_hash = hash_token(token)

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    if not db_token:
        return None
    if db_token.revoked:
        return None
    if db_token.expires_at < datetime.utcnow():
        return None

    # Update last_used_at
    db_token.last_used_at = datetime.utcnow()
    db.commit()

    return db_token

# Revoke a single refresh token
def revoke_refresh_token(db: Session, token: str):
    """Revoke a single refresh token."""
    token_hash = hash_token(token)
    db_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )
    if db_token:
        db_token.revoked = True
        db.commit()

# Revoke all refresh tokens for a user
def revoke_all_user_tokens(db: Session, user_id):
    """Logout all user tokens or detect compromise"""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id
    ).update({"revoked": True})
    db.commit()

# Retrieve all active sessions for a user
def get_user_active_sessions(db: Session, user_id) -> list:
    """Retrieve all active sessions for a user."""
    return db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).all()

def cleanup_expired_tokens(db: Session):
    """Delete all expired or revoked tokens periodically"""
    from sqlalchemy import or_
    db.query(RefreshToken).filter(
        or_(
            RefreshToken.expires_at < datetime.utcnow(),
            RefreshToken.revoked == True
        )
    ).delete()
    db.commit()