from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User
from app.schemas.account import CreateAccountRequest, AccountResponse
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: CreateAccountRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Open a new bank account (SAVINGS or CURRENT) for the authenticated customer."""
    ip = get_client_ip(request)
    service = AccountService(db)
    return service.create_account(current_user.id, account_data, ip_address=ip)


@router.get("", response_model=List[AccountResponse])
def get_my_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all accounts belonging to the authenticated customer."""
    service = AccountService(db)
    return service.get_accounts_for_user(current_user.id)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account_details(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """View details of a specific account (must belong to authenticated customer)."""
    service = AccountService(db)
    return service.get_account_details(account_id, current_user.id)
