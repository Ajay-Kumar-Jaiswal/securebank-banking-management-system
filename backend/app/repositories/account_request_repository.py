from typing import Optional, List
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.account_request import AccountClosureRequest
from app.models.account import Account
from app.models.user import User


class AccountRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, request_id: int) -> Optional[AccountClosureRequest]:
        return (
            self.db.query(AccountClosureRequest)
            .options(
                joinedload(AccountClosureRequest.user),
                joinedload(AccountClosureRequest.account),
                joinedload(AccountClosureRequest.reviewer),
            )
            .filter(AccountClosureRequest.id == request_id)
            .first()
        )

    def list_for_user(self, user_id: int) -> List[AccountClosureRequest]:
        return (
            self.db.query(AccountClosureRequest)
            .options(
                joinedload(AccountClosureRequest.user),
                joinedload(AccountClosureRequest.account),
            )
            .filter(AccountClosureRequest.user_id == user_id)
            .order_by(AccountClosureRequest.requested_at.desc())
            .all()
        )

    def list_all(self, status: Optional[str] = None, request_type: Optional[str] = None) -> List[AccountClosureRequest]:
        query = (
            self.db.query(AccountClosureRequest)
            .options(
                joinedload(AccountClosureRequest.user),
                joinedload(AccountClosureRequest.account),
                joinedload(AccountClosureRequest.reviewer),
            )
        )
        if status:
            query = query.filter(AccountClosureRequest.status == status.upper())
        if request_type:
            query = query.filter(AccountClosureRequest.request_type == request_type.upper())
        return query.order_by(AccountClosureRequest.requested_at.desc()).all()

    def has_pending_request(self, account_id: int, request_type: Optional[str] = None) -> bool:
        query = self.db.query(AccountClosureRequest.id).filter(
            AccountClosureRequest.account_id == account_id,
            AccountClosureRequest.status == "PENDING",
        )
        if request_type:
            query = query.filter(AccountClosureRequest.request_type == request_type.upper())
        return query.first() is not None

    def create(self, req: AccountClosureRequest) -> AccountClosureRequest:
        self.db.add(req)
        self.db.flush()
        return req

    def update(self, req: AccountClosureRequest) -> AccountClosureRequest:
        self.db.flush()
        return req

    def count_pending(self) -> int:
        return (
            self.db.query(func.count(AccountClosureRequest.id))
            .filter(AccountClosureRequest.status == "PENDING")
            .scalar()
            or 0
        )
