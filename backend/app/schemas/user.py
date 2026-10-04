from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, field_validator
from app.schemas.validators import validate_phone_number


class UserResponse(BaseModel):
    userId: int
    fullName: str
    email: str
    phoneNumber: str
    address: Optional[str] = ""
    role: str
    status: str
    createdAt: datetime

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_orm(cls, user):
        return cls(
            userId=user.id,
            fullName=user.full_name,
            email=user.email,
            phoneNumber=user.phone_number,
            address=user.address or "",
            role=user.role,
            status=user.status,
            createdAt=user.created_at,
        )


class UpdateProfileRequest(BaseModel):
    fullName: Optional[str] = Field(None, min_length=2, max_length=150, validation_alias=AliasChoices("fullName", "full_name"))
    phoneNumber: Optional[str] = Field(None, validation_alias=AliasChoices("phoneNumber", "phone_number"))
    address: Optional[str] = Field(None, max_length=255)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("phoneNumber")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_phone_number(v, required=False)


class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(..., min_length=1, validation_alias=AliasChoices("currentPassword", "current_password"))
    newPassword: str = Field(..., min_length=6, max_length=100, validation_alias=AliasChoices("newPassword", "new_password"))

    model_config = ConfigDict(populate_by_name=True)
