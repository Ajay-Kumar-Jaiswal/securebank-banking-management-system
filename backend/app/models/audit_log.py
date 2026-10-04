from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column("audit_id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    actor_user_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)

    # Relationship
    actor = relationship("User", foreign_keys=[actor_user_id])
