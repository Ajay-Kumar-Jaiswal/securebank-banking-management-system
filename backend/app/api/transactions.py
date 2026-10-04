from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User
from app.schemas.transaction import (
    DepositRequest,
    WithdrawRequest,
    TransferRequest,
    TransactionResponse,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/deposit", response_model=TransactionResponse)
def deposit(
    deposit_data: DepositRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deposit money into customer's account."""
    ip = get_client_ip(request)
    service = TransactionService(db)
    return service.deposit(current_user.id, deposit_data, ip_address=ip)


@router.post("/withdraw", response_model=TransactionResponse)
def withdraw(
    withdraw_data: WithdrawRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Withdraw money from customer's account."""
    ip = get_client_ip(request)
    service = TransactionService(db)
    return service.withdraw(current_user.id, withdraw_data, ip_address=ip)


@router.post("/transfer", response_model=TransactionResponse)
def transfer(
    transfer_data: TransferRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Atomically transfer money from customer's account to a destination account."""
    ip = get_client_ip(request)
    service = TransactionService(db)
    return service.transfer(current_user.id, transfer_data, ip_address=ip)


@router.get("", response_model=List[TransactionResponse])
def get_transactions(
    accountId: int = Query(..., description="ID of the account to query transactions for"),
    type: Optional[str] = Query(None, description="Filter by transaction type"),
    from_date: Optional[datetime] = Query(None, alias="from", description="ISO start date filter"),
    to_date: Optional[datetime] = Query(None, alias="to", description="ISO end date filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List transaction history for an account owned by the authenticated customer."""
    service = TransactionService(db)
    return service.get_transactions_for_account(
        account_id=accountId,
        requesting_user_id=current_user.id,
        transaction_type=type,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction_details(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """View details of a specific transaction."""
    service = TransactionService(db)
    return service.get_transaction_details(transaction_id, current_user.id)
