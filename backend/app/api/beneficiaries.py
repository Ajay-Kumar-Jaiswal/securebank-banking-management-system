from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_client_ip
from app.models.user import User
from app.schemas.beneficiary import BeneficiaryRequest, BeneficiaryResponse
from app.services.beneficiary_service import BeneficiaryService

router = APIRouter(prefix="/beneficiaries", tags=["Beneficiaries"])


@router.post("", response_model=BeneficiaryResponse, status_code=status.HTTP_201_CREATED)
def add_beneficiary(
    beneficiary_data: BeneficiaryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a validated beneficiary payee for the authenticated customer."""
    ip = get_client_ip(request)
    service = BeneficiaryService(db)
    return service.add_beneficiary(current_user.id, beneficiary_data, ip_address=ip)


@router.get("", response_model=List[BeneficiaryResponse])
def get_beneficiaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List saved beneficiaries for the authenticated customer."""
    service = BeneficiaryService(db)
    return service.list_for_user(current_user.id)


@router.put("/{beneficiary_id}", response_model=BeneficiaryResponse)
def update_beneficiary(
    beneficiary_id: int,
    beneficiary_data: BeneficiaryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update details of a saved beneficiary."""
    ip = get_client_ip(request)
    service = BeneficiaryService(db)
    return service.update_beneficiary(beneficiary_id, current_user.id, beneficiary_data, ip_address=ip)


@router.delete("/{beneficiary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_beneficiary(
    beneficiary_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a saved beneficiary."""
    ip = get_client_ip(request)
    service = BeneficiaryService(db)
    service.delete_beneficiary(beneficiary_id, current_user.id, ip_address=ip)
    return None
