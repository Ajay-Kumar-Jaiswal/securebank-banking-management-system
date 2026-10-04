from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_client_ip, get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, LoginResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    request_data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register a new customer account."""
    ip = get_client_ip(request)
    service = AuthService(db)
    created = service.register(request_data, ip_address=ip)
    return {
        "userId": created.id,
        "email": created.email,
        "message": "Registration successful. Please log in.",
    }


@router.post("/login", response_model=LoginResponse)
def login(
    request_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate user credentials and receive a JWT access token."""
    ip = get_client_ip(request)
    service = AuthService(db)
    return service.login(request_data, ip_address=ip)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Get the currently authenticated user's profile details."""
    return UserResponse.from_orm(current_user)
