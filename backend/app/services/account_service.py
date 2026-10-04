from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.account import Account
from app.schemas.account import CreateAccountRequest, AccountResponse
from app.repositories.account_repository import AccountRepository
from app.repositories.user_repository import UserRepository
from app.core.exceptions import (
    AccountNotFoundException,
    UserNotFoundException,
    UnauthorizedAccountAccessException,
    DuplicateAccountException,
)
from app.utils.generators import generate_account_number
from app.services.audit_service import AuditService
from app.services.email_service import EmailService


class AccountService:
    def __init__(self, db: Session):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.user_repo = UserRepository(db)
        self.audit_service = AuditService(db)
        self.email_service = EmailService(db)

    def create_account(self, user_id: int, request: CreateAccountRequest, ip_address: Optional[str] = None) -> AccountResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User not found with id: {user_id}")

        account_number = self._generate_unique_account_number()
        account = Account(
            account_number=account_number,
            user_id=user.id,
            account_type=request.accountType,
            balance=Decimal("0.00"),
            status="ACTIVE",
            version=0,
        )
        saved = self.account_repo.create(account)
        self.db.commit()
        self.db.refresh(saved)

        self.audit_service.log(
            action="ACCOUNT_CREATION",
            entity_type="ACCOUNT",
            entity_id=str(saved.id),
            description=f"Account {saved.account_number} ({saved.account_type}) opened for {user.email}",
            actor_user_id=user.id,
            ip_address=ip_address,
        )

        # Send confirmation email
        self.email_service.send_account_created_email(
            full_name=user.full_name,
            email=user.email,
            account_number=saved.account_number,
            account_type=saved.account_type,
            created_at=saved.created_at,
        )

        return self.to_response(saved)

    def get_accounts_for_user(self, user_id: int) -> List[AccountResponse]:
        accounts = self.account_repo.list_for_user(user_id)
        return [self.to_response(acc) for acc in accounts]

    def get_account_details(self, account_id: int, requesting_user_id: int) -> AccountResponse:
        account = self.get_owned_account_or_throw(account_id, requesting_user_id)
        return self.to_response(account)

    def get_owned_account_or_throw(self, account_id: int, requesting_user_id: int, for_update: bool = False) -> Account:
        account = self.account_repo.get_by_id(account_id, for_update=for_update)
        if not account:
            raise AccountNotFoundException(f"Account not found with id: {account_id}")

        if account.user_id != requesting_user_id:
            raise UnauthorizedAccountAccessException("You do not have permission to access this account.")

        return account

    def get_account_by_number_or_throw(self, account_number: str, for_update: bool = False) -> Account:
        account = self.account_repo.get_by_number(account_number, for_update=for_update)
        if not account:
            raise AccountNotFoundException(f"Account not found with number: {account_number}")
        return account

    def _generate_unique_account_number(self) -> str:
        for _ in range(10):
            candidate = generate_account_number()
            if not self.account_repo.exists_by_number(candidate):
                return candidate
        raise DuplicateAccountException("Could not generate a unique account number, please retry.")

    def to_response(self, account: Account) -> AccountResponse:
        return AccountResponse(
            accountId=account.id,
            accountNumber=account.account_number,
            customerId=account.user_id,
            customerName=account.user.full_name if account.user else "",
            accountType=account.account_type,
            balance=account.balance,
            status=account.status,
            createdAt=account.created_at,
        )
