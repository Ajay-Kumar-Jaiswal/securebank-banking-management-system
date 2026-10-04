from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_admin, get_client_ip
from app.models.user import User
from app.schemas.user import UserResponse
from app.schemas.account import AccountResponse
from app.schemas.transaction import TransactionResponse
from app.schemas.account_request import AccountClosureResponse, ClosureReviewRequest
from app.schemas.admin import (
    AdminDashboardStats,
    CustomerDetailResponse,
    UpdateAccountStatusRequest,
    UpdateCustomerStatusRequest,
)
from app.schemas.audit_log import AuditLogResponse
from app.services.admin_service import AdminService
from app.services.account_request_service import AccountRequestService

router = APIRouter(prefix="/admin", tags=["Admin Portal"])


@router.get("/dashboard", response_model=AdminDashboardStats)
def get_dashboard_metrics(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retrieve bank-wide overview statistics, volumes, and recent activity."""
    service = AdminService(db)
    return service.get_dashboard_stats()


@router.get("/customers", response_model=List[UserResponse])
def get_customers(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, SUSPENDED, DEACTIVATED)"),
    role: Optional[str] = Query(None, description="Filter by role (CUSTOMER, ADMIN)"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List and search all customers."""
    service = AdminService(db)
    return service.get_all_customers(search=search, status=status, role=role)


@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse)
def get_customer_details(
    customer_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """View full profile, all accounts, and recent transactions for a customer."""
    service = AdminService(db)
    return service.get_customer_details(customer_id)


@router.put("/customers/{customer_id}/status", response_model=UserResponse)
def update_customer_status(
    customer_id: int,
    status_data: UpdateCustomerStatusRequest,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update a customer's status (ACTIVE, SUSPENDED, DEACTIVATED)."""
    ip = get_client_ip(request)
    service = AdminService(db)
    return service.update_customer_status(customer_id, status_data, admin_user_id=admin.id, ip_address=ip)


@router.get("/administrators", response_model=List[UserResponse])
def get_administrators(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all system administrators."""
    service = AdminService(db)
    return service.get_all_administrators()


@router.put("/administrators/{admin_id}/status", response_model=UserResponse)
def update_administrator_status(
    admin_id: int,
    status_data: UpdateCustomerStatusRequest,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update an administrator's status (ACTIVE, SUSPENDED, DEACTIVATED)."""
    ip = get_client_ip(request)
    service = AdminService(db)
    return service.update_administrator_status(admin_id, status_data, admin_user_id=admin.id, ip_address=ip)



@router.get("/accounts", response_model=List[AccountResponse])
def get_accounts(
    search: Optional[str] = Query(None, description="Search by account number or customer name"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, SUSPENDED, CLOSED)"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List and search all accounts bank-wide."""
    service = AdminService(db)
    return service.get_all_accounts(search=search, status=status)


@router.put("/accounts/{account_id}/status", response_model=AccountResponse)
def update_account_status(
    account_id: int,
    status_data: UpdateAccountStatusRequest,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Suspend, reactivate, or close an account."""
    ip = get_client_ip(request)
    service = AdminService(db)
    return service.update_account_status(account_id, status_data, admin_user_id=admin.id, ip_address=ip)


@router.get("/transactions", response_model=List[TransactionResponse])
def get_all_transactions(
    type: Optional[str] = Query(None, description="Filter by transaction type"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all transactions executed across the bank."""
    service = AdminService(db)
    return service.get_all_transactions(transaction_type=type)


@router.get("/account-requests", response_model=List[AccountClosureResponse])
@router.get("/closure-requests", response_model=List[AccountClosureResponse])
def get_account_requests(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, APPROVED, REJECTED, CANCELLED)"),
    request_type: Optional[str] = Query(None, description="Filter by request type (CLOSURE, REOPEN)"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List account closure and reopen requests submitted by customers."""
    service = AccountRequestService(db)
    return service.list_all_requests(status=status, request_type=request_type)


@router.post("/account-requests/{request_id}/approve", response_model=AccountClosureResponse)
@router.post("/closure-requests/{request_id}/approve", response_model=AccountClosureResponse)
def approve_account_request(
    request_id: int,
    review_data: ClosureReviewRequest,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Approve a pending account request (CLOSURE -> CLOSED, REOPEN -> ACTIVE)."""
    ip = get_client_ip(request)
    service = AccountRequestService(db)
    return service.approve_request(request_id, admin_user_id=admin.id, review_req=review_data, ip_address=ip)


@router.post("/account-requests/{request_id}/reject", response_model=AccountClosureResponse)
@router.post("/closure-requests/{request_id}/reject", response_model=AccountClosureResponse)
def reject_account_request(
    request_id: int,
    review_data: ClosureReviewRequest,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Reject a pending account request: account status remains unchanged."""
    ip = get_client_ip(request)
    service = AccountRequestService(db)
    return service.reject_request(request_id, admin_user_id=admin.id, review_req=review_data, ip_address=ip)


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action name"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    search: Optional[str] = Query(None, description="Search description or entity ID"),
    limit: int = Query(100, ge=1, le=500),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Query system and financial audit logs."""
    service = AdminService(db)
    return service.get_audit_logs(action=action, entity_type=entity_type, search=search, limit=limit)
