from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column("email_log_id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    recipient_email = Column(String(150), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="SENT")  # SENT, FAILED, SKIPPED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
