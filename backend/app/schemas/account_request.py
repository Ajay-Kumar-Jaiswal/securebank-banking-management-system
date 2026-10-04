from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, field_validator


class AccountClosureCreateRequest(BaseModel):
    accountId: int = Field(..., validation_alias=AliasChoices("accountId", "account_id"))
    reason: str = Field(..., min_length=5, max_length=255)
    additionalNotes: Optional[str] = Field(None, max_length=1000, validation_alias=AliasChoices("additionalNotes", "additional_notes"))
    confirmationCheckbox: bool = Field(default=True, validation_alias=AliasChoices("confirmationCheckbox", "confirmation_checkbox"))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("confirmationCheckbox")
    @classmethod
    def validate_confirmation(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must confirm that you wish to close this account.")
        return v


class AccountReopenCreateRequest(BaseModel):
    accountId: int = Field(..., validation_alias=AliasChoices("accountId", "account_id"))
    reason: str = Field(..., min_length=5, max_length=255)
    additionalNotes: Optional[str] = Field(None, max_length=1000, validation_alias=AliasChoices("additionalNotes", "additional_notes"))
    confirmationCheckbox: bool = Field(default=True, validation_alias=AliasChoices("confirmationCheckbox", "confirmation_checkbox"))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("confirmationCheckbox")
    @classmethod
    def validate_confirmation(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must confirm that you wish to reopen this account.")
        return v


class AccountClosureResponse(BaseModel):
    id: int
    requestId: Optional[int] = None
    userId: int
    customerName: str
    customerEmail: str
    accountId: int
    accountNumber: str
    accountType: str
    balance: Decimal
    reason: str
    additionalNotes: Optional[str] = None
    status: str
    requestType: str = Field(default="CLOSURE", validation_alias=AliasChoices("requestType", "request_type"))
    adminNotes: Optional[str] = None
    reviewedBy: Optional[int] = None
    requestedAt: datetime
    reviewedAt: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)

    def __init__(self, **data):
        if "requestId" not in data and "id" in data:
            data["requestId"] = data["id"]
        elif "id" not in data and "requestId" in data:
            data["id"] = data["requestId"]
        if "requestType" not in data and "request_type" in data:
            data["requestType"] = data["request_type"]
        elif "requestType" not in data:
            data["requestType"] = "CLOSURE"
        super().__init__(**data)


class ClosureReviewRequest(BaseModel):
    adminNotes: Optional[str] = Field(None, max_length=1000, validation_alias=AliasChoices("adminNotes", "admin_notes"))

    model_config = ConfigDict(populate_by_name=True)


AccountRequestReviewRequest = ClosureReviewRequest
AccountRequestResponse = AccountClosureResponse

