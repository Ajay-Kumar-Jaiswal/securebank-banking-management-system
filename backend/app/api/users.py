from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User
from app.schemas.user import UserResponse, UpdateProfileRequest, ChangePasswordRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Retrieve personal profile details."""
    return UserResponse.from_orm(current_user)


@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: UpdateProfileRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update personal profile information."""
    ip = get_client_ip(request)
    service = AuthService(db)
    updated = service.update_profile(current_user.id, profile_data, ip_address=ip)
    return UserResponse.from_orm(updated)


@router.post("/change-password")
def change_password(
    pwd_data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change account password."""
    ip = get_client_ip(request)
    service = AuthService(db)
    service.change_password(current_user.id, pwd_data, ip_address=ip)
    return {"message": "Password changed successfully."}
