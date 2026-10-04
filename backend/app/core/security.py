from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with random salt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash (supports $2a$ and $2b$)."""
    try:
        plain_bytes = plain_password.encode("utf-8")
        # Normalize $2a$ to $2b$ if necessary for modern bcrypt implementations
        normalized_hash = hashed_password
        if normalized_hash.startswith("$2a$"):
            normalized_hash = "$2b$" + normalized_hash[4:]
        return bcrypt.checkpw(plain_bytes, normalized_hash.encode("utf-8"))
    except Exception:
        # Fallback to direct check if normalization wasn't needed
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "iat": now,
        "exp": expire,
        "iss": "securebank-api",
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer="securebank-api",
    )
