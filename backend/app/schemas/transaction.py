from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, field_validator


class DepositRequest(BaseModel):
    accountId: int = Field(..., validation_alias=AliasChoices("accountId", "account_id"))
    amount: Decimal
    description: Optional[str] = "Deposit"

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0.00"):
            raise ValueError("Amount must be greater than zero.")
        return v


class WithdrawRequest(BaseModel):
    accountId: int = Field(..., validation_alias=AliasChoices("accountId", "account_id"))
    amount: Decimal
    description: Optional[str] = "Withdrawal"

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0.00"):
            raise ValueError("Amount must be greater than zero.")
        return v


class TransferRequest(BaseModel):
    fromAccountId: int = Field(..., validation_alias=AliasChoices("fromAccountId", "from_account_id"))
    toAccountNumber: str = Field(..., min_length=5, validation_alias=AliasChoices("toAccountNumber", "to_account_number"))
    amount: Decimal
    description: Optional[str] = "Fund transfer"

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0.00"):
            raise ValueError("Amount must be greater than zero.")
        return v


class TransactionResponse(BaseModel):
    transactionId: int
    transactionReference: str
    accountId: int
    accountNumber: str
    amount: Decimal
    balanceBefore: Optional[Decimal] = None
    balanceAfter: Optional[Decimal] = None
    transactionType: str
    description: Optional[str] = ""
    status: str
    relatedAccountId: Optional[int] = None
    createdAt: datetime

    model_config = ConfigDict(populate_by_name=True)
