from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User
from app.schemas.account_request import (
    AccountClosureCreateRequest,
    AccountReopenCreateRequest,
    AccountClosureResponse,
)
from app.services.account_request_service import AccountRequestService

router = APIRouter(prefix="/account-requests", tags=["Account Requests"])


@router.post("/closure", response_model=AccountClosureResponse, status_code=status.HTTP_201_CREATED)
def create_closure_request(
    request_data: AccountClosureCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Customer submits an account closure request. Balance must be exactly 0.00."""
    ip = get_client_ip(request)
    service = AccountRequestService(db)
    return service.create_closure_request(current_user.id, request_data, ip_address=ip)


@router.post("/reopen", response_model=AccountClosureResponse, status_code=status.HTTP_201_CREATED)
def create_reopen_request(
    request_data: AccountReopenCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Customer submits an account reopen request for a CLOSED account."""
    ip = get_client_ip(request)
    service = AccountRequestService(db)
    return service.create_reopen_request(current_user.id, request_data, ip_address=ip)



@router.get("/my", response_model=List[AccountClosureResponse])
def get_my_closure_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List closure requests submitted by the authenticated customer."""
    service = AccountRequestService(db)
    return service.list_user_requests(current_user.id)
