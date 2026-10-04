from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, AliasChoices


class BeneficiaryRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    accountNumber: str = Field(..., min_length=5, max_length=20, validation_alias=AliasChoices("accountNumber", "account_number"))
    bankName: str = Field(default="SecureBank", min_length=2, max_length=150, validation_alias=AliasChoices("bankName", "bank_name"))
    ifscCode: str = Field(default="SEC0001234", min_length=4, max_length=20, validation_alias=AliasChoices("ifscCode", "ifsc_code"))

    model_config = ConfigDict(populate_by_name=True)


class BeneficiaryResponse(BaseModel):
    beneficiaryId: int
    name: str
    accountNumber: str
    bankName: str
    ifscCode: str
    createdAt: datetime

    model_config = ConfigDict(populate_by_name=True)
