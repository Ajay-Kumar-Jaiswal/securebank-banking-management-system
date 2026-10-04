from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, field_validator


class CreateAccountRequest(BaseModel):
    accountType: str = Field(..., validation_alias=AliasChoices("accountType", "account_type"))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("accountType")
    @classmethod
    def validate_type(cls, v: str) -> str:
        upper = v.strip().upper()
        if upper not in ("SAVINGS", "CURRENT"):
            raise ValueError("Account type must be either SAVINGS or CURRENT.")
        return upper


class AccountResponse(BaseModel):
    accountId: int
    accountNumber: str
    customerId: int
    customerName: str
    accountType: str
    balance: Decimal
    status: str
    createdAt: datetime

    model_config = ConfigDict(populate_by_name=True)
