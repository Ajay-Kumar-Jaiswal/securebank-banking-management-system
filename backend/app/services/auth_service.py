from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, LoginResponse
from app.schemas.user import UpdateProfileRequest, ChangePasswordRequest
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    UserNotFoundException,
    BankingException,
)
from app.services.audit_service import AuditService
from app.services.email_service import EmailService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_service = AuditService(db)
        self.email_service = EmailService(db)

    def register(self, request: RegisterRequest, ip_address: Optional[str] = None) -> User:
        if getattr(request, "role", None) and request.role.strip().upper() == "ADMIN":
            raise BankingException(
                "Registration with ADMIN role is not permitted.",
                status_code=400,
                error_code="ADMIN_REGISTRATION_FORBIDDEN",
            )

        if self.user_repo.exists_by_email(request.email):
            raise DuplicateEmailException(f"An account with email '{request.email}' already exists.")

        user = User(
            full_name=request.fullName,
            email=request.email.strip().lower(),
            phone_number=request.phoneNumber,
            password_hash=hash_password(request.password),
            address=request.address or "",
            role="CUSTOMER",
            status="ACTIVE",
        )
        created_user = self.user_repo.create(user)
        self.db.commit()
        self.db.refresh(created_user)

        self.audit_service.log(
            action="USER_REGISTRATION",
            entity_type="USER",
            entity_id=str(created_user.id),
            description=f"User registered with email {created_user.email}",
            actor_user_id=created_user.id,
            ip_address=ip_address,
        )

        # Trigger welcome email (non-blocking failure safe)
        self.email_service.send_welcome_email(created_user.full_name, created_user.email)

        return created_user

    def login(self, request: LoginRequest, ip_address: Optional[str] = None) -> LoginResponse:
        user = self.user_repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.password_hash):
            self.audit_service.log(
                action="FAILED_LOGIN",
                entity_type="USER",
                entity_id=request.email,
                description=f"Failed login attempt for {request.email}",
                actor_user_id=None,
                ip_address=ip_address,
            )
            raise InvalidCredentialsException("Invalid email or password.")

        if user.status == "DEACTIVATED":
            raise BankingException("Account has been deactivated.", status_code=403, error_code="ACCOUNT_DEACTIVATED")
        if user.status == "SUSPENDED":
            raise BankingException("Your account is currently suspended. Please contact bank administration.", status_code=403, error_code="ACCOUNT_SUSPENDED")

        token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        })

        self.audit_service.log(
            action="USER_LOGIN",
            entity_type="USER",
            entity_id=str(user.id),
            description=f"User {user.email} logged in successfully",
            actor_user_id=user.id,
            ip_address=ip_address,
        )

        return LoginResponse(
            token=token,
            tokenType="Bearer",
            userId=user.id,
            fullName=user.full_name,
            email=user.email,
            role=user.role,
            status=user.status,
        )

    def update_profile(self, user_id: int, request: UpdateProfileRequest, ip_address: Optional[str] = None) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        if request.fullName is not None:
            user.full_name = request.fullName
        if request.phoneNumber is not None:
            user.phone_number = request.phoneNumber
        if request.address is not None:
            user.address = request.address

        self.user_repo.update(user)
        self.db.commit()
        self.db.refresh(user)

        self.audit_service.log(
            action="PROFILE_UPDATE",
            entity_type="USER",
            entity_id=str(user.id),
            description=f"User {user.email} updated profile",
            actor_user_id=user.id,
            ip_address=ip_address,
        )

        return user

    def change_password(self, user_id: int, request: ChangePasswordRequest, ip_address: Optional[str] = None) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        if not verify_password(request.currentPassword, user.password_hash):
            raise InvalidCredentialsException("Current password does not match.")

        user.password_hash = hash_password(request.newPassword)
        self.user_repo.update(user)
        self.db.commit()

        self.audit_service.log(
            action="PASSWORD_CHANGE",
            entity_type="USER",
            entity_id=str(user.id),
            description=f"User {user.email} changed password",
            actor_user_id=user.id,
            ip_address=ip_address,
        )
