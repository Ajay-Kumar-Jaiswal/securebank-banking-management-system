from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, field_validator
from app.schemas.user import UserResponse
from app.schemas.account import AccountResponse
from app.schemas.transaction import TransactionResponse
from app.schemas.account_request import AccountClosureResponse


class UpdateAccountStatusRequest(BaseModel):
    status: str

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        upper = v.strip().upper()
        if upper not in ("ACTIVE", "SUSPENDED", "CLOSED"):
            raise ValueError("Status must be one of ACTIVE, SUSPENDED, CLOSED.")
        return upper


class UpdateCustomerStatusRequest(BaseModel):
    status: str

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        upper = v.strip().upper()
        if upper not in ("ACTIVE", "SUSPENDED", "DEACTIVATED"):
            raise ValueError("Status must be one of ACTIVE, SUSPENDED, DEACTIVATED.")
        return upper


class CustomerDetailResponse(BaseModel):
    customer: UserResponse
    user: Optional[UserResponse] = None
    accounts: List[AccountResponse] = []
    recentTransactions: List[TransactionResponse] = []
    totalTransactionsCount: int = 0
    closureRequests: List[AccountClosureResponse] = []
    accountRequests: List[AccountClosureResponse] = []

    model_config = ConfigDict(populate_by_name=True)

    def __init__(self, **data):
        if "user" not in data and "customer" in data:
            data["user"] = data["customer"]
        elif "customer" not in data and "user" in data:
            data["customer"] = data["user"]
        if "accountRequests" in data and ("closureRequests" not in data or not data["closureRequests"]):
            data["closureRequests"] = data["accountRequests"]
        elif "closureRequests" in data and ("accountRequests" not in data or not data["accountRequests"]):
            data["accountRequests"] = data["closureRequests"]
        super().__init__(**data)


class AdminDashboardStats(BaseModel):
    totalCustomers: int
    activeCustomers: int
    suspendedCustomers: int
    totalAccounts: int
    activeAccounts: int
    pendingClosureRequests: int
    totalDepositsCount: int
    totalDepositsAmount: Decimal
    totalWithdrawalsCount: int
    totalWithdrawalsAmount: Decimal
    totalTransfersCount: int
    totalTransfersAmount: Decimal
    bankWideBalance: Decimal
    recentTransactions: List[TransactionResponse]
    recentCustomers: List[UserResponse]

    model_config = ConfigDict(populate_by_name=True)
