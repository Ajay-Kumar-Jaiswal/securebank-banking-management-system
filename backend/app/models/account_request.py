from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class AccountClosureRequest(Base):
    __tablename__ = "account_closure_requests"

    id = Column("closure_request_id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id"), nullable=False, index=True)
    account_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("accounts.account_id"), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    additional_notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)  # PENDING, APPROVED, REJECTED, CANCELLED
    request_type = Column(String(20), nullable=False, default="CLOSURE", server_default="CLOSURE", index=True)  # CLOSURE, REOPEN
    admin_notes = Column(Text, nullable=True)
    reviewed_by = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id"), nullable=True)
    requested_at = Column(DateTime, default=utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="closure_requests")
    account = relationship("Account", foreign_keys=[account_id], back_populates="closure_requests")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
