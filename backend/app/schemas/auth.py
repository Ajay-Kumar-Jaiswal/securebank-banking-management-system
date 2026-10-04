from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, AliasChoices, field_validator


from app.schemas.validators import validate_phone_number


class RegisterRequest(BaseModel):
    fullName: str = Field(..., min_length=2, max_length=150, validation_alias=AliasChoices("fullName", "full_name"))
    email: EmailStr
    phoneNumber: str = Field(..., validation_alias=AliasChoices("phoneNumber", "phone_number"))
    password: str = Field(..., min_length=6, max_length=100)
    address: Optional[str] = Field(default="", max_length=255)
    role: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("phoneNumber")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_phone_number(v, required=True)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

    model_config = ConfigDict(populate_by_name=True)


class LoginResponse(BaseModel):
    token: str
    accessToken: Optional[str] = None
    tokenType: str = "Bearer"
    userId: int
    fullName: str
    email: str
    role: str
    status: str

    model_config = ConfigDict(populate_by_name=True)

    def __init__(self, **data):
        if "accessToken" not in data and "token" in data:
            data["accessToken"] = data["token"]
        elif "token" not in data and "accessToken" in data:
            data["token"] = data["accessToken"]
        super().__init__(**data)

