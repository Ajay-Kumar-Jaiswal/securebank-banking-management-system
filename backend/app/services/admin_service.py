from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.account import Account
from app.schemas.user import UserResponse
from app.schemas.account import AccountResponse
from app.schemas.transaction import TransactionResponse
from app.schemas.admin import (
    AdminDashboardStats,
    CustomerDetailResponse,
    UpdateAccountStatusRequest,
    UpdateCustomerStatusRequest,
)
from app.schemas.audit_log import AuditLogResponse
from app.repositories.user_repository import UserRepository
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.account_request_repository import AccountRequestRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.account_service import AccountService
from app.services.transaction_service import TransactionService
from app.services.audit_service import AuditService
from app.core.exceptions import (
    UserNotFoundException,
    AccountNotFoundException,
    InvalidTransactionException,
    BankingException,
)


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.account_repo = AccountRepository(db)
        self.tx_repo = TransactionRepository(db)
        self.req_repo = AccountRequestRepository(db)
        self.audit_repo = AuditLogRepository(db)
        self.account_service = AccountService(db)
        self.tx_service = TransactionService(db)
        self.audit_service = AuditService(db)

    def get_dashboard_stats(self) -> AdminDashboardStats:
        total_customers = self.user_repo.count_by_role("CUSTOMER")
        active_customers = self.user_repo.count_by_role_and_status("CUSTOMER", "ACTIVE")
        suspended_customers = self.user_repo.count_by_role_and_status("CUSTOMER", "SUSPENDED")

        total_accounts = self.account_repo.count_all()
        active_accounts = self.account_repo.count_by_status("ACTIVE")
        pending_closures = self.req_repo.count_pending()

        tx_stats = self.tx_repo.get_summary_stats()
        total_balance = Decimal(str(self.account_repo.get_total_balance()))

        recent_txs = self.tx_repo.list_all(limit=10)
        recent_customers = self.user_repo.list_all(role="CUSTOMER", limit=10)

        return AdminDashboardStats(
            totalCustomers=total_customers,
            activeCustomers=active_customers,
            suspendedCustomers=suspended_customers,
            totalAccounts=total_accounts,
            activeAccounts=active_accounts,
            pendingClosureRequests=pending_closures,
            totalDepositsCount=tx_stats["deposits_count"],
            totalDepositsAmount=tx_stats["deposits_sum"],
            totalWithdrawalsCount=tx_stats["withdrawals_count"],
            totalWithdrawalsAmount=tx_stats["withdrawals_sum"],
            totalTransfersCount=tx_stats["transfers_count"],
            totalTransfersAmount=tx_stats["transfers_sum"],
            bankWideBalance=total_balance,
            recentTransactions=[self.tx_service.to_response(tx) for tx in recent_txs],
            recentCustomers=[UserResponse.from_orm(c) for c in recent_customers],
        )

    def get_all_customers(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        role: Optional[str] = None,
    ) -> List[UserResponse]:
        users = self.user_repo.list_all(search=search, status=status, role=role)
        return [UserResponse.from_orm(u) for u in users]

    def get_customer_details(self, customer_id: int) -> CustomerDetailResponse:
        user = self.user_repo.get_by_id(customer_id)
        if not user:
            raise UserNotFoundException(f"Customer with ID {customer_id} not found.")

        accounts = self.account_repo.list_for_user(customer_id)
        all_txs = []
        total_tx_count = 0
        for acc in accounts:
            txs = self.tx_repo.list_for_account(acc.id, limit=500)
            total_tx_count += len(txs)
            all_txs.extend(txs)

        all_txs.sort(key=lambda x: x.created_at, reverse=True)

        from app.services.account_request_service import AccountRequestService
        req_service = AccountRequestService(self.db)
        user_reqs = self.req_repo.list_for_user(customer_id)
        req_responses = [req_service.to_response(r) for r in user_reqs]

        user_resp = UserResponse.from_orm(user)

        return CustomerDetailResponse(
            customer=user_resp,
            user=user_resp,
            accounts=[self.account_service.to_response(a) for a in accounts],
            recentTransactions=[self.tx_service.to_response(t) for t in all_txs[:20]],
            totalTransactionsCount=total_tx_count,
            closureRequests=req_responses,
            accountRequests=req_responses,
        )

    def _update_user_status_core(
        self,
        target_user: User,
        new_status: str,
        current_admin_id: int,
        ip_address: Optional[str] = None,
    ) -> UserResponse:
        # 1. Check if target user is already in requested status
        if target_user.status == new_status:
            if target_user.role == "ADMIN":
                if new_status == "DEACTIVATED":
                    raise BankingException(
                        "Administrator is already deactivated.",
                        status_code=400,
                        error_code="ALREADY_DEACTIVATED",
                    )
                if new_status == "ACTIVE":
                    raise BankingException(
                        "Administrator is already active.",
                        status_code=400,
                        error_code="ALREADY_ACTIVE",
                    )
            return UserResponse.from_orm(target_user)

        # 2. Prevent Last Admin Lockout
        if target_user.role == "ADMIN" and target_user.status == "ACTIVE" and new_status in ["DEACTIVATED", "SUSPENDED"]:
            active_admins = self.user_repo.count_by_role_and_status("ADMIN", "ACTIVE")
            if active_admins <= 1:
                if target_user.id == current_admin_id:
                    self.audit_service.log(
                        action="ADMIN_SELF_DEACTIVATION_BLOCKED",
                        entity_type="USER",
                        entity_id=str(target_user.id),
                        description=f"Admin {current_admin_id} ({target_user.email}) attempted to deactivate their own administrator account (blocked by last active admin protection)",
                        actor_user_id=current_admin_id,
                        ip_address=ip_address,
                    )
                    self.db.commit()
                raise BankingException(
                    "Cannot deactivate the last active administrator. Create or activate another administrator first.",
                    status_code=400,
                    error_code="LAST_ADMIN_PROTECTION",
                )

        # 3. Prevent Admin Self-Deactivation (when multiple active admins exist)
        if target_user.id == current_admin_id and new_status in ["DEACTIVATED", "SUSPENDED"]:
            self.audit_service.log(
                action="ADMIN_SELF_DEACTIVATION_BLOCKED",
                entity_type="USER",
                entity_id=str(target_user.id),
                description=f"Admin {current_admin_id} ({target_user.email}) attempted to deactivate their own administrator account",
                actor_user_id=current_admin_id,
                ip_address=ip_address,
            )
            self.db.commit()
            raise BankingException(
                "You cannot deactivate your own administrator account.",
                status_code=400,
                error_code="ADMIN_SELF_DEACTIVATION_FORBIDDEN",
            )

        # 4. Perform update
        old_status = target_user.status
        target_user.status = new_status
        self.user_repo.update(target_user)
        self.db.commit()
        self.db.refresh(target_user)

        # 5. Audit Logging
        if target_user.role == "ADMIN":
            if new_status == "DEACTIVATED":
                action = "ADMIN_DEACTIVATED"
                description = f"Administrator {target_user.email} deactivated by admin {current_admin_id}"
            elif new_status == "ACTIVE":
                action = "ADMIN_ACTIVATED"
                description = f"Administrator {target_user.email} reactivated by admin {current_admin_id}"
            else:
                action = f"ADMIN_STATUS_{new_status}"
                description = f"Administrator {target_user.email} status changed from {old_status} to {new_status} by admin {current_admin_id}"
        else:
            action = f"CUSTOMER_STATUS_{new_status}"
            description = f"Admin {current_admin_id} changed user {target_user.email} status from {old_status} to {new_status}"

        self.audit_service.log(
            action=action,
            entity_type="USER",
            entity_id=str(target_user.id),
            description=description,
            actor_user_id=current_admin_id,
            ip_address=ip_address,
        )
        self.db.commit()

        return UserResponse.from_orm(target_user)

    def update_customer_status(
        self,
        customer_id: int,
        request: UpdateCustomerStatusRequest,
        admin_user_id: int,
        ip_address: Optional[str] = None,
    ) -> UserResponse:
        user = self.user_repo.get_by_id(customer_id)
        if not user:
            raise UserNotFoundException(f"Customer with ID {customer_id} not found.")
        return self._update_user_status_core(user, request.status, admin_user_id, ip_address)

    def get_all_administrators(self) -> List[UserResponse]:
        admins = self.user_repo.list_all(role="ADMIN")
        return [UserResponse.from_orm(u) for u in admins]

    def update_administrator_status(
        self,
        admin_id: int,
        request: UpdateCustomerStatusRequest,
        admin_user_id: int,
        ip_address: Optional[str] = None,
    ) -> UserResponse:
        user = self.user_repo.get_by_id(admin_id)
        if not user:
            raise UserNotFoundException(f"Administrator with ID {admin_id} not found.")
        if user.role != "ADMIN":
            raise BankingException("Target user is not an administrator.", status_code=400)
        return self._update_user_status_core(user, request.status, admin_user_id, ip_address)

    def get_all_accounts(self, search: Optional[str] = None, status: Optional[str] = None) -> List[AccountResponse]:
        accounts = self.account_repo.list_all(search=search, status=status)
        return [self.account_service.to_response(a) for a in accounts]

    def update_account_status(
        self,
        account_id: int,
        request: UpdateAccountStatusRequest,
        admin_user_id: int,
        ip_address: Optional[str] = None,
    ) -> AccountResponse:
        account = self.account_repo.get_by_id(account_id)
        if not account:
            raise AccountNotFoundException(f"Account with ID {account_id} not found.")

        # Business rule check when closing an account
        if request.status == "CLOSED" and account.balance > Decimal("0.00"):
            raise InvalidTransactionException("Cannot close an account with a non-zero balance.")

        old_status = account.status
        account.status = request.status
        self.account_repo.update(account)
        self.db.commit()
        self.db.refresh(account)

        self.audit_service.log(
            action=f"ACCOUNT_STATUS_{request.status}",
            entity_type="ACCOUNT",
            entity_id=str(account.id),
            description=f"Admin {admin_user_id} changed account {account.account_number} status from {old_status} to {account.status}",
            actor_user_id=admin_user_id,
            ip_address=ip_address,
        )
        self.db.commit()

        return self.account_service.to_response(account)

    def get_all_transactions(self, transaction_type: Optional[str] = None) -> List[TransactionResponse]:
        txs = self.tx_repo.list_all(transaction_type=transaction_type, limit=200)
        return [self.tx_service.to_response(tx) for tx in txs]

    def get_audit_logs(
        self,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLogResponse]:
        logs = self.audit_repo.list_all(action=action, entity_type=entity_type, search=search, limit=limit)
        return [
            AuditLogResponse(
                id=l.id,
                actorUserId=l.actor_user_id,
                actorName=l.actor.full_name if l.actor else None,
                action=l.action,
                entityType=l.entity_type,
                entityId=l.entity_id,
                description=l.description,
                ipAddress=l.ip_address,
                timestamp=l.timestamp,
            )
            for l in logs
        ]
