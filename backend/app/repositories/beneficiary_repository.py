from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.beneficiary import Beneficiary


class BeneficiaryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, beneficiary_id: int) -> Optional[Beneficiary]:
        return self.db.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()

    def get_by_id_and_user_id(self, beneficiary_id: int, user_id: int) -> Optional[Beneficiary]:
        return (
            self.db.query(Beneficiary)
            .filter(Beneficiary.id == beneficiary_id, Beneficiary.user_id == user_id)
            .first()
        )

    def list_for_user(self, user_id: int) -> List[Beneficiary]:
        return (
            self.db.query(Beneficiary)
            .filter(Beneficiary.user_id == user_id)
            .order_by(Beneficiary.name.asc())
            .all()
        )

    def create(self, beneficiary: Beneficiary) -> Beneficiary:
        self.db.add(beneficiary)
        self.db.flush()
        return beneficiary

    def update(self, beneficiary: Beneficiary) -> Beneficiary:
        self.db.flush()
        return beneficiary

    def delete(self, beneficiary: Beneficiary) -> None:
        self.db.delete(beneficiary)
        self.db.flush()
