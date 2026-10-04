from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column("beneficiary_id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    account_number = Column(String(20), nullable=False)
    bank_name = Column(String(150), nullable=False)
    ifsc_code = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="beneficiaries")
