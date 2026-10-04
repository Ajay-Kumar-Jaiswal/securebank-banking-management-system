from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column("transaction_id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    transaction_reference = Column(String(40), nullable=False, index=True)
    account_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("accounts.account_id"), nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False)  # DEPOSIT, WITHDRAWAL, TRANSFER_IN, TRANSFER_OUT, TRANSFER
    amount = Column(Numeric(19, 2), nullable=False)
    balance_before = Column(Numeric(19, 2), nullable=True)
    balance_after = Column(Numeric(19, 2), nullable=True)
    description = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="SUCCESS")  # SUCCESS, FAILED, PENDING
    related_account_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("accounts.account_id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)

    # Relationships
    account = relationship("Account", foreign_keys=[account_id], back_populates="transactions")
    related_account = relationship("Account", foreign_keys=[related_account_id])
