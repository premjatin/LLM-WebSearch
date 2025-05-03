from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode = {"exp": expire, "sub": str(subject)} # 'sub' is the standard claim for subject (user identifier)
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verifies a token and returns the subject (e.g., username) if valid, otherwise None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        subject: Optional[str] = payload.get("sub")
        if subject is None:
            return None
        # You could add more checks here, e.g., token type, scope etc.
        return subject
    except JWTError: # Catches expired tokens, invalid signatures etc.
        return None