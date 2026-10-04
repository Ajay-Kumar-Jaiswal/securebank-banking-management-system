from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.transaction import (
    DepositRequest,
    WithdrawRequest,
    TransferRequest,
    TransactionResponse,
)
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.account_service import AccountService
from app.services.audit_service import AuditService
from app.services.email_service import EmailService
from app.core.exceptions import (
    InvalidTransactionException,
    InsufficientBalanceException,
    InvalidAccountStatusException,
    AccountNotFoundException,
)
from app.utils.generators import generate_transaction_reference


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.tx_repo = TransactionRepository(db)
        self.account_service = AccountService(db)
        self.audit_service = AuditService(db)
        self.email_service = EmailService(db)

    def deposit(self, requesting_user_id: int, request: DepositRequest, ip_address: Optional[str] = None) -> TransactionResponse:
        account = self.account_service.get_owned_account_or_throw(request.accountId, requesting_user_id, for_update=True)
        self._assert_active(account)

        amount = self._validate_amount(request.amount)
        balance_before = account.balance
        account.balance = balance_before + amount
        if account.version is not None:
            account.version += 1

        reference = generate_transaction_reference()
        tx = Transaction(
            transaction_reference=reference,
            account_id=account.id,
            transaction_type="DEPOSIT",
            amount=amount,
            balance_before=balance_before,
            balance_after=account.balance,
            description=request.description or "Deposit",
            status="SUCCESS",
        )

        self.tx_repo.create(tx)
        self.account_repo.update(account)
        self.db.commit()
        self.db.refresh(tx)

        self.audit_service.log(
            action="DEPOSIT",
            entity_type="TRANSACTION",
            entity_id=reference,
            description=f"Deposited ₹{amount:,.2f} to account {account.account_number}",
            actor_user_id=requesting_user_id,
            ip_address=ip_address,
        )

        # Trigger notification email safely
        if account.user:
            self.email_service.send_deposit_email(
                full_name=account.user.full_name,
                email=account.user.email,
                account_number=account.account_number,
                amount=amount,
                prev_balance=balance_before,
                new_balance=account.balance,
                reference=reference,
                created_at=tx.created_at,
            )

        return self.to_response(tx)

    def withdraw(self, requesting_user_id: int, request: WithdrawRequest, ip_address: Optional[str] = None) -> TransactionResponse:
        account = self.account_service.get_owned_account_or_throw(request.accountId, requesting_user_id, for_update=True)
        self._assert_active(account)

        amount = self._validate_amount(request.amount)
        if account.balance < amount:
            raise InsufficientBalanceException("Insufficient balance for this withdrawal.")

        balance_before = account.balance
        account.balance = balance_before - amount
        if account.version is not None:
            account.version += 1

        reference = generate_transaction_reference()
        tx = Transaction(
            transaction_reference=reference,
            account_id=account.id,
            transaction_type="WITHDRAWAL",
            amount=amount,
            balance_before=balance_before,
            balance_after=account.balance,
            description=request.description or "Withdrawal",
            status="SUCCESS",
        )

        self.tx_repo.create(tx)
        self.account_repo.update(account)
        self.db.commit()
        self.db.refresh(tx)

        self.audit_service.log(
            action="WITHDRAWAL",
            entity_type="TRANSACTION",
            entity_id=reference,
            description=f"Withdrew ₹{amount:,.2f} from account {account.account_number}",
            actor_user_id=requesting_user_id,
            ip_address=ip_address,
        )

        # Trigger notification email safely
        if account.user:
            self.email_service.send_withdrawal_email(
                full_name=account.user.full_name,
                email=account.user.email,
                account_number=account.account_number,
                amount=amount,
                prev_balance=balance_before,
                new_balance=account.balance,
                reference=reference,
                created_at=tx.created_at,
            )

        return self.to_response(tx)

    def transfer(self, requesting_user_id: int, request: TransferRequest, ip_address: Optional[str] = None) -> TransactionResponse:
        # Pre-lookup receiver to check validity
        receiver_candidate = self.account_repo.get_by_number(request.toAccountNumber)
        if not receiver_candidate:
            raise AccountNotFoundException(f"Destination account '{request.toAccountNumber}' not found.")

        if receiver_candidate.id == request.fromAccountId:
            raise InvalidTransactionException("Cannot transfer money to the same account.")

        amount = self._validate_amount(request.amount)

        # Lock both accounts in consistent ascending order of ID to prevent deadlocks
        first_id, second_id = sorted([request.fromAccountId, receiver_candidate.id])
        acc1 = self.account_repo.get_by_id(first_id, for_update=True)
        acc2 = self.account_repo.get_by_id(second_id, for_update=True)

        sender = acc1 if acc1.id == request.fromAccountId else acc2
        receiver = acc2 if acc1.id == request.fromAccountId else acc1

        # Authorization check: sender must belong to logged-in user
        if sender.user_id != requesting_user_id:
            raise InvalidTransactionException("You do not have permission to transfer from this account.")

        self._assert_active(sender)
        self._assert_active(receiver)

        if sender.balance < amount:
            raise InsufficientBalanceException("Insufficient balance for this transfer.")

        sender_balance_before = sender.balance
        sender.balance = sender_balance_before - amount
        if sender.version is not None:
            sender.version += 1

        receiver_balance_before = receiver.balance
        receiver.balance = receiver_balance_before + amount
        if receiver.version is not None:
            receiver.version += 1

        shared_ref = generate_transaction_reference()
        desc = request.description or "Fund transfer"

        # Sender leg (TRANSFER_OUT)
        debit_tx = Transaction(
            transaction_reference=shared_ref,
            account_id=sender.id,
            transaction_type="TRANSFER_OUT",
            amount=amount,
            balance_before=sender_balance_before,
            balance_after=sender.balance,
            description=f"{desc} to {receiver.account_number}",
            status="SUCCESS",
            related_account_id=receiver.id,
        )

        # Receiver leg (TRANSFER_IN)
        credit_tx = Transaction(
            transaction_reference=shared_ref,
            account_id=receiver.id,
            transaction_type="TRANSFER_IN",
            amount=amount,
            balance_before=receiver_balance_before,
            balance_after=receiver.balance,
            description=f"{desc} from {sender.account_number}",
            status="SUCCESS",
            related_account_id=sender.id,
        )

        self.tx_repo.create(debit_tx)
        self.tx_repo.create(credit_tx)
        self.account_repo.update(sender)
        self.account_repo.update(receiver)

        # Atomic commit
        self.db.commit()
        self.db.refresh(debit_tx)

        self.audit_service.log(
            action="TRANSFER",
            entity_type="TRANSACTION",
            entity_id=shared_ref,
            description=f"Transferred ₹{amount:,.2f} from {sender.account_number} to {receiver.account_number}",
            actor_user_id=requesting_user_id,
            ip_address=ip_address,
        )

        # Emails (post-commit, failures will not roll back transaction)
        if sender.user:
            self.email_service.send_transfer_sender_email(
                sender_name=sender.user.full_name,
                sender_email=sender.user.email,
                source_account=sender.account_number,
                dest_account=receiver.account_number,
                amount=amount,
                prev_balance=sender_balance_before,
                new_balance=sender.balance,
                reference=shared_ref,
                created_at=debit_tx.created_at,
            )

        if receiver.user:
            self.email_service.send_transfer_receiver_email(
                receiver_name=receiver.user.full_name,
                receiver_email=receiver.user.email,
                dest_account=receiver.account_number,
                amount=amount,
                new_balance=receiver.balance,
                reference=shared_ref,
                created_at=debit_tx.created_at,
            )

        return self.to_response(debit_tx)

    def get_transactions_for_account(
        self,
        account_id: int,
        requesting_user_id: int,
        transaction_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[TransactionResponse]:
        # Assert ownership
        self.account_service.get_owned_account_or_throw(account_id, requesting_user_id)
        txs = self.tx_repo.list_for_account(
            account_id=account_id,
            transaction_type=transaction_type,
            from_date=from_date,
            to_date=to_date,
        )
        return [self.to_response(tx) for tx in txs]

    def get_transaction_details(self, transaction_id: int, requesting_user_id: int) -> TransactionResponse:
        tx = self.tx_repo.get_by_id(transaction_id)
        if not tx:
            raise InvalidTransactionException(f"Transaction not found with id: {transaction_id}")

        # Assert ownership of the account involved
        self.account_service.get_owned_account_or_throw(tx.account_id, requesting_user_id)
        return self.to_response(tx)

    def _assert_active(self, account: Account):
        if account.status != "ACTIVE":
            raise InvalidAccountStatusException(
                f"Account {account.account_number} is {account.status} and cannot be used for transactions."
            )

    def _validate_amount(self, amount: Decimal) -> Decimal:
        if amount is None or amount <= Decimal("0.00"):
            raise InvalidTransactionException("Amount must be greater than zero.")
        return amount

    def to_response(self, tx: Transaction) -> TransactionResponse:
        return TransactionResponse(
            transactionId=tx.id,
            transactionReference=tx.transaction_reference,
            accountId=tx.account_id,
            accountNumber=tx.account.account_number if tx.account else "",
            amount=tx.amount,
            balanceBefore=tx.balance_before,
            balanceAfter=tx.balance_after,
            transactionType=tx.transaction_type,
            description=tx.description or "",
            status=tx.status,
            relatedAccountId=tx.related_account_id,
            createdAt=tx.created_at,
        )
