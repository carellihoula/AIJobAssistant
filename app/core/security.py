"""
Security utilities: safe password hashing + JWT.
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings 

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Use argon2
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

# ------------------ PASSWORD ------------------ #
def get_password_hash(password: str) -> str:
    """
    Hash a password safely using argon2
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password safely.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ------------------ JWT ------------------ #
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Create JWT token with expiration.
    """
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str):
    """
    Decode and verify JWT token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
