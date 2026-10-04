from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.account_request import AccountClosureRequest
from app.schemas.account_request import (
    AccountClosureCreateRequest,
    AccountReopenCreateRequest,
    AccountClosureResponse,
    ClosureReviewRequest,
)
from app.repositories.account_request_repository import AccountRequestRepository
from app.repositories.account_repository import AccountRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.email_service import EmailService
from app.core.exceptions import (
    ClosureRequestException,
    AccountNotFoundException,
    UnauthorizedAccountAccessException,
)


class AccountRequestService:
    def __init__(self, db: Session):
        self.db = db
        self.request_repo = AccountRequestRepository(db)
        self.account_repo = AccountRepository(db)
        self.user_repo = UserRepository(db)
        self.audit_service = AuditService(db)
        self.email_service = EmailService(db)

    def create_closure_request(
        self,
        user_id: int,
        request: AccountClosureCreateRequest,
        ip_address: Optional[str] = None,
    ) -> AccountClosureResponse:
        account = self.account_repo.get_by_id(request.accountId)
        if not account:
            raise AccountNotFoundException(f"Account with ID {request.accountId} not found.")

        if account.user_id != user_id:
            raise UnauthorizedAccountAccessException("You do not have permission to close this account.")

        if account.status != "ACTIVE":
            raise ClosureRequestException(f"Account is currently {account.status}. Only ACTIVE accounts can be requested for closure.")

        if account.balance != Decimal("0.00"):
            raise ClosureRequestException("Please withdraw or transfer your remaining balance before requesting account closure.")

        if self.request_repo.has_pending_request(account.id, request_type="CLOSURE"):
            raise ClosureRequestException("A pending closure request already exists for this account.")

        closure_req = AccountClosureRequest(
            user_id=user_id,
            account_id=account.id,
            reason=request.reason.strip(),
            additional_notes=request.additionalNotes.strip() if request.additionalNotes else None,
            status="PENDING",
            request_type="CLOSURE",
            requested_at=datetime.now(timezone.utc),
        )
        saved = self.request_repo.create(closure_req)
        self.db.commit()
        self.db.refresh(saved)

        self.audit_service.log(
            action="CLOSURE_REQUEST_SUBMITTED",
            entity_type="ACCOUNT_CLOSURE_REQUEST",
            entity_id=str(saved.id),
            description=f"Closure request submitted for account {account.account_number}",
            actor_user_id=user_id,
            ip_address=ip_address,
        )

        # Send confirmation email
        if account.user:
            self.email_service.send_closure_request_received_email(
                full_name=account.user.full_name,
                email=account.user.email,
                account_number=account.account_number,
            )

        return self.to_response(saved)

    def create_reopen_request(
        self,
        user_id: int,
        request: AccountReopenCreateRequest,
        ip_address: Optional[str] = None,
    ) -> AccountClosureResponse:
        account = self.account_repo.get_by_id(request.accountId)
        if not account:
            raise AccountNotFoundException(f"Account with ID {request.accountId} not found.")

        if account.user_id != user_id:
            raise UnauthorizedAccountAccessException("You do not have permission to reopen this account.")

        if account.status != "CLOSED":
            raise ClosureRequestException(f"Account is currently {account.status}. Only CLOSED accounts can be requested to reopen.")

        if self.request_repo.has_pending_request(account.id, request_type="REOPEN"):
            raise ClosureRequestException("A pending reopen request already exists for this account.")

        reopen_req = AccountClosureRequest(
            user_id=user_id,
            account_id=account.id,
            reason=request.reason.strip(),
            additional_notes=request.additionalNotes.strip() if request.additionalNotes else None,
            status="PENDING",
            request_type="REOPEN",
            requested_at=datetime.now(timezone.utc),
        )
        saved = self.request_repo.create(reopen_req)
        self.db.commit()
        self.db.refresh(saved)

        self.audit_service.log(
            action="REOPEN_REQUEST_SUBMITTED",
            entity_type="ACCOUNT_REOPEN_REQUEST",
            entity_id=str(saved.id),
            description=f"Reopen request submitted for account {account.account_number}",
            actor_user_id=user_id,
            ip_address=ip_address,
        )

        # Send confirmation email
        if account.user:
            self.email_service.send_reopen_request_received_email(
                full_name=account.user.full_name,
                email=account.user.email,
                account_number=account.account_number,
            )

        return self.to_response(saved)

    def list_user_requests(self, user_id: int) -> List[AccountClosureResponse]:
        reqs = self.request_repo.list_for_user(user_id)
        return [self.to_response(r) for r in reqs]

    def list_all_requests(
        self,
        status: Optional[str] = None,
        request_type: Optional[str] = None,
    ) -> List[AccountClosureResponse]:
        reqs = self.request_repo.list_all(status=status, request_type=request_type)
        return [self.to_response(r) for r in reqs]

    def approve_request(
        self,
        request_id: int,
        admin_user_id: int,
        review_req: ClosureReviewRequest,
        ip_address: Optional[str] = None,
    ) -> AccountClosureResponse:
        req = self.request_repo.get_by_id(request_id)
        if not req:
            raise ClosureRequestException(f"Account request {request_id} not found.")

        if req.status != "PENDING":
            raise ClosureRequestException(f"Cannot approve request with status '{req.status}'.")

        account = req.account
        if not account:
            account = self.account_repo.get_by_id(req.account_id)

        req_type = getattr(req, "request_type", "CLOSURE") or "CLOSURE"

        if req_type == "CLOSURE":
            if account.balance != Decimal("0.00"):
                raise ClosureRequestException("Account balance must be zero before approving closure.")
            account.status = "CLOSED"
            action_name = "CLOSURE_REQUEST_APPROVED"
            audit_desc = f"Account {account.account_number} closed by admin {admin_user_id}"
        elif req_type == "REOPEN":
            account.status = "ACTIVE"
            action_name = "REOPEN_REQUEST_APPROVED"
            audit_desc = f"Account {account.account_number} reopened by admin {admin_user_id}"
        else:
            raise ClosureRequestException(f"Unsupported request type: {req_type}")

        self.account_repo.update(account)

        req.status = "APPROVED"
        req.admin_notes = review_req.adminNotes
        req.reviewed_by = admin_user_id
        req.reviewed_at = datetime.now(timezone.utc)
        self.request_repo.update(req)

        self.db.commit()
        self.db.refresh(req)

        self.audit_service.log(
            action=action_name,
            entity_type="ACCOUNT_REQUEST",
            entity_id=str(req.id),
            description=audit_desc,
            actor_user_id=admin_user_id,
            ip_address=ip_address,
        )

        # Trigger corresponding notification email
        if req.user:
            if req_type == "CLOSURE":
                self.email_service.send_closure_approved_email(
                    full_name=req.user.full_name,
                    email=req.user.email,
                    account_number=account.account_number,
                    admin_notes=req.admin_notes,
                )
            else:
                self.email_service.send_reopen_approved_email(
                    full_name=req.user.full_name,
                    email=req.user.email,
                    account_number=account.account_number,
                    admin_notes=req.admin_notes,
                )

        return self.to_response(req)

    def approve_closure_request(
        self,
        request_id: int,
        admin_user_id: int,
        review_req: ClosureReviewRequest,
        ip_address: Optional[str] = None,
    ) -> AccountClosureResponse:
        return self.approve_request(request_id, admin_user_id, review_req, ip_address)

    def reject_request(
        self,
        request_id: int,
        admin_user_id: int,
        review_req: ClosureReviewRequest,
        ip_address: Optional[str] = None,
    ) -> AccountClosureResponse:
        req = self.request_repo.get_by_id(request_id)
        if not req:
            raise ClosureRequestException(f"Account request {request_id} not found.")

        if req.status != "PENDING":
            raise ClosureRequestException(f"Cannot reject request with status '{req.status}'.")

        req_type = getattr(req, "request_type", "CLOSURE") or "CLOSURE"

        req.status = "REJECTED"
        req.admin_notes = review_req.adminNotes or "Request rejected by administrator."
        req.reviewed_by = admin_user_id
        req.reviewed_at = datetime.now(timezone.utc)
        self.request_repo.update(req)

        self.db.commit()
        self.db.refresh(req)

        acc_num = req.account.account_number if req.account else str(req.account_id)
        action_name = "CLOSURE_REQUEST_REJECTED" if req_type == "CLOSURE" else "REOPEN_REQUEST_REJECTED"
        audit_desc = f"{req_type.capitalize()} request for account {acc_num} rejected by admin {admin_user_id}"

        self.audit_service.log(
            action=action_name,
            entity_type="ACCOUNT_REQUEST",
            entity_id=str(req.id),
            description=audit_desc,
            actor_user_id=admin_user_id,
            ip_address=ip_address,
        )

        # Trigger rejection email
        if req.user:
            if req_type == "CLOSURE":
                self.email_service.send_closure_rejected_email(
                    full_name=req.user.full_name,
                    email=req.user.email,
                    account_number=acc_num,
                    reason=req.admin_notes,
                )
            else:
                self.email_service.send_reopen_rejected_email(
                    full_name=req.user.full_name,
                    email=req.user.email,
                    account_number=acc_num,
                    reason=req.admin_notes,
                )

        return self.to_response(req)

    def reject_closure_request(
        self,
        request_id: int,
        admin_user_id: int,
        review_req: ClosureReviewRequest,
        ip_address: Optional[str] = None,
    ) -> AccountClosureResponse:
        return self.reject_request(request_id, admin_user_id, review_req, ip_address)

    def to_response(self, r: AccountClosureRequest) -> AccountClosureResponse:
        req_type = getattr(r, "request_type", "CLOSURE") or "CLOSURE"
        return AccountClosureResponse(
            id=r.id,
            userId=r.user_id,
            customerName=r.user.full_name if r.user else "",
            customerEmail=r.user.email if r.user else "",
            accountId=r.account_id,
            accountNumber=r.account.account_number if r.account else "",
            accountType=r.account.account_type if r.account else "",
            balance=r.account.balance if r.account else Decimal("0.00"),
            reason=r.reason,
            additionalNotes=r.additional_notes,
            status=r.status,
            requestType=req_type,
            adminNotes=r.admin_notes,
            reviewedBy=r.reviewed_by,
            requestedAt=r.requested_at,
            reviewedAt=r.reviewed_at,
        )
