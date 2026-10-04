from typing import Optional, List
from sqlalchemy import or_, func, select
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()

    def exists_by_email(self, email: str) -> bool:
        return self.db.query(User.id).filter(func.lower(User.email) == email.strip().lower()).first() is not None

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user: User) -> User:
        self.db.flush()
        return user

    def list_all(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[User]:
        query = self.db.query(User)
        if search:
            needle = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(User.full_name).like(needle),
                    func.lower(User.email).like(needle),
                    User.phone_number.like(needle),
                )
            )
        if role:
            query = query.filter(User.role == role.upper())
        if status:
            query = query.filter(User.status == status.upper())

        return query.order_by(User.id.desc()).offset(offset).limit(limit).all()

    def count_by_role(self, role: str) -> int:
        return self.db.query(func.count(User.id)).filter(User.role == role.upper()).scalar() or 0

    def count_by_role_and_status(self, role: str, status: str) -> int:
        return (
            self.db.query(func.count(User.id))
            .filter(User.role == role.upper(), User.status == status.upper())
            .scalar()
            or 0
        )
