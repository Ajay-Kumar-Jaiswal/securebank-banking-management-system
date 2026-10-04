from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column("user_id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    phone_number = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True, default="")
    role = Column(String(20), nullable=False, default="CUSTOMER")  # CUSTOMER, ADMIN
    status = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE, SUSPENDED, DEACTIVATED
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=True)

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    beneficiaries = relationship("Beneficiary", back_populates="user", cascade="all, delete-orphan")
    closure_requests = relationship(
        "AccountClosureRequest",
        back_populates="user",
        foreign_keys="AccountClosureRequest.user_id",
        cascade="all, delete-orphan"
    )
