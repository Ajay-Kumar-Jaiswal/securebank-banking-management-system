from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, BigInteger, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"

    id = Column("account_id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    account_number = Column(String(20), nullable=False, unique=True, index=True)
    user_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id"), nullable=False, index=True)
    account_type = Column(String(20), nullable=False)  # SAVINGS, CURRENT
    balance = Column(Numeric(19, 2), nullable=False, default=Decimal("0.00"))
    status = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE, SUSPENDED, CLOSED, PENDING
    version = Column(BigInteger().with_variant(Integer, "sqlite"), default=0, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=True)

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship(
        "Transaction",
        back_populates="account",
        foreign_keys="Transaction.account_id",
        cascade="all, delete-orphan",
        order_by="desc(Transaction.created_at)"
    )
    closure_requests = relationship(
        "AccountClosureRequest",
        back_populates="account",
        foreign_keys="AccountClosureRequest.account_id",
        cascade="all, delete-orphan"
    )
