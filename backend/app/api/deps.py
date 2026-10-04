from typing import Generator, Optional
from fastapi import Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import (
    InvalidCredentialsException,
    PermissionDeniedException,
    UserNotFoundException,
)
from app.repositories.user_repository import UserRepository
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    """Extract client IP, handling proxies (X-Forwarded-For)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate JWT, returning the authenticated User."""
    if not credentials or not credentials.credentials:
        raise InvalidCredentialsException("Authentication token required.")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise InvalidCredentialsException("Invalid token payload.")
        user_id = int(user_id_str)
    except Exception:
        raise InvalidCredentialsException("Invalid or expired authentication token.")

    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise UserNotFoundException("User associated with token not found.")

    if user.status == "DEACTIVATED":
        raise PermissionDeniedException("Account has been deactivated.")
    if user.status == "SUSPENDED":
        raise PermissionDeniedException("Account is currently suspended.")

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Enforce ADMIN role authorization."""
    if current_user.role != "ADMIN":
        raise PermissionDeniedException("Insufficient permissions.")
    return current_user
