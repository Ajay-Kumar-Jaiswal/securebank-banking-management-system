from typing import Optional, List
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload
from app.models.account import Account
from app.models.user import User


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def _apply_lock(self, query, for_update: bool):
        if for_update and self.db.bind and self.db.bind.dialect.name != "sqlite":
            return query.with_for_update()
        return query

    def get_by_id(self, account_id: int, for_update: bool = False) -> Optional[Account]:
        query = self.db.query(Account).options(joinedload(Account.user)).filter(Account.id == account_id)
        query = self._apply_lock(query, for_update)
        return query.first()

    def get_by_number(self, account_number: str, for_update: bool = False) -> Optional[Account]:
        query = self.db.query(Account).options(joinedload(Account.user)).filter(Account.account_number == account_number.strip())
        query = self._apply_lock(query, for_update)
        return query.first()

    def exists_by_number(self, account_number: str) -> bool:
        return self.db.query(Account.id).filter(Account.account_number == account_number.strip()).first() is not None

    def list_for_user(self, user_id: int) -> List[Account]:
        return (
            self.db.query(Account)
            .options(joinedload(Account.user))
            .filter(Account.user_id == user_id)
            .order_by(Account.id.asc())
            .all()
        )

    def list_all(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Account]:
        query = self.db.query(Account).join(User, Account.user_id == User.id).options(joinedload(Account.user))
        if search:
            needle = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Account.account_number).like(needle),
                    func.lower(User.full_name).like(needle),
                    func.lower(User.email).like(needle),
                )
            )
        if status:
            query = query.filter(Account.status == status.upper())

        return query.order_by(Account.id.desc()).offset(offset).limit(limit).all()

    def create(self, account: Account) -> Account:
        self.db.add(account)
        self.db.flush()
        return account

    def update(self, account: Account) -> Account:
        self.db.flush()
        return account

    def count_all(self) -> int:
        return self.db.query(func.count(Account.id)).scalar() or 0

    def count_by_status(self, status: str) -> int:
        return self.db.query(func.count(Account.id)).filter(Account.status == status.upper()).scalar() or 0

    def get_total_balance(self) -> float:
        val = self.db.query(func.sum(Account.balance)).scalar()
        return val or 0.0
