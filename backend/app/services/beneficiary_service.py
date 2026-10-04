from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.beneficiary import Beneficiary
from app.schemas.beneficiary import BeneficiaryRequest, BeneficiaryResponse
from app.repositories.beneficiary_repository import BeneficiaryRepository
from app.repositories.account_repository import AccountRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.core.exceptions import (
    BeneficiaryNotFoundException,
    UserNotFoundException,
    AccountNotFoundException,
    InvalidAccountStatusException,
)


class BeneficiaryService:
    def __init__(self, db: Session):
        self.db = db
        self.beneficiary_repo = BeneficiaryRepository(db)
        self.account_repo = AccountRepository(db)
        self.user_repo = UserRepository(db)
        self.audit_service = AuditService(db)

    def add_beneficiary(self, user_id: int, request: BeneficiaryRequest, ip_address: Optional[str] = None) -> BeneficiaryResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User not found with id: {user_id}")

        # Check destination account exists and is ACTIVE
        destination = self.account_repo.get_by_number(request.accountNumber)
        if not destination:
            raise AccountNotFoundException(f"No account found with number: {request.accountNumber}")

        if destination.status != "ACTIVE":
            raise InvalidAccountStatusException("Destination account is not active and cannot be added as a beneficiary.")

        beneficiary = Beneficiary(
            user_id=user.id,
            name=request.name.strip(),
            account_number=request.accountNumber.strip(),
            bank_name=request.bankName.strip(),
            ifsc_code=request.ifscCode.strip(),
        )
        saved = self.beneficiary_repo.create(beneficiary)
        self.db.commit()
        self.db.refresh(saved)

        self.audit_service.log(
            action="BENEFICIARY_ADDED",
            entity_type="BENEFICIARY",
            entity_id=str(saved.id),
            description=f"Beneficiary '{saved.name}' ({saved.account_number}) added by {user.email}",
            actor_user_id=user.id,
            ip_address=ip_address,
        )

        return self.to_response(saved)

    def list_for_user(self, user_id: int) -> List[BeneficiaryResponse]:
        beneficiaries = self.beneficiary_repo.list_for_user(user_id)
        return [self.to_response(b) for b in beneficiaries]

    def update_beneficiary(
        self,
        beneficiary_id: int,
        user_id: int,
        request: BeneficiaryRequest,
        ip_address: Optional[str] = None,
    ) -> BeneficiaryResponse:
        b = self.beneficiary_repo.get_by_id_and_user_id(beneficiary_id, user_id)
        if not b:
            raise BeneficiaryNotFoundException()

        # If account number changed, re-validate
        if b.account_number != request.accountNumber:
            destination = self.account_repo.get_by_number(request.accountNumber)
            if not destination or destination.status != "ACTIVE":
                raise AccountNotFoundException(f"Target account '{request.accountNumber}' does not exist or is not active.")
            b.account_number = request.accountNumber.strip()

        b.name = request.name.strip()
        b.bank_name = request.bankName.strip()
        b.ifsc_code = request.ifscCode.strip()

        self.beneficiary_repo.update(b)
        self.db.commit()
        self.db.refresh(b)

        self.audit_service.log(
            action="BENEFICIARY_UPDATED",
            entity_type="BENEFICIARY",
            entity_id=str(b.id),
            description=f"Beneficiary {b.id} updated by user {user_id}",
            actor_user_id=user_id,
            ip_address=ip_address,
        )

        return self.to_response(b)

    def delete_beneficiary(self, beneficiary_id: int, user_id: int, ip_address: Optional[str] = None) -> None:
        b = self.beneficiary_repo.get_by_id_and_user_id(beneficiary_id, user_id)
        if not b:
            raise BeneficiaryNotFoundException()

        self.beneficiary_repo.delete(b)
        self.db.commit()

        self.audit_service.log(
            action="BENEFICIARY_DELETED",
            entity_type="BENEFICIARY",
            entity_id=str(beneficiary_id),
            description=f"Beneficiary {beneficiary_id} deleted by user {user_id}",
            actor_user_id=user_id,
            ip_address=ip_address,
        )

    def to_response(self, b: Beneficiary) -> BeneficiaryResponse:
        return BeneficiaryResponse(
            beneficiaryId=b.id,
            name=b.name,
            accountNumber=b.account_number,
            bankName=b.bank_name,
            ifscCode=b.ifsc_code,
            createdAt=b.created_at,
        )
