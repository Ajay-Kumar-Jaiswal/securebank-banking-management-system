from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.transaction import Transaction
from app.models.account import Account


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        return (
            self.db.query(Transaction)
            .options(joinedload(Transaction.account).joinedload(Account.user))
            .filter(Transaction.id == transaction_id)
            .first()
        )

    def get_by_reference(self, reference: str) -> List[Transaction]:
        return (
            self.db.query(Transaction)
            .options(joinedload(Transaction.account).joinedload(Account.user))
            .filter(Transaction.transaction_reference == reference)
            .all()
        )

    def list_for_account(
        self,
        account_id: int,
        transaction_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Transaction]:
        query = (
            self.db.query(Transaction)
            .options(joinedload(Transaction.account).joinedload(Account.user))
            .filter(Transaction.account_id == account_id)
        )
        if transaction_type:
            # Match exact or prefix (e.g. "TRANSFER" matching "TRANSFER", "TRANSFER_IN", "TRANSFER_OUT")
            t_upper = transaction_type.upper()
            if t_upper == "TRANSFER":
                query = query.filter(Transaction.transaction_type.in_(["TRANSFER", "TRANSFER_IN", "TRANSFER_OUT"]))
            else:
                query = query.filter(Transaction.transaction_type == t_upper)

        if from_date:
            query = query.filter(Transaction.created_at >= from_date)
        if to_date:
            query = query.filter(Transaction.created_at <= to_date)

        return query.order_by(Transaction.created_at.desc(), Transaction.id.desc()).offset(offset).limit(limit).all()

    def list_all(
        self,
        transaction_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Transaction]:
        query = (
            self.db.query(Transaction)
            .options(joinedload(Transaction.account).joinedload(Account.user))
        )
        if transaction_type:
            t_upper = transaction_type.upper()
            if t_upper == "TRANSFER":
                query = query.filter(Transaction.transaction_type.in_(["TRANSFER", "TRANSFER_IN", "TRANSFER_OUT"]))
            else:
                query = query.filter(Transaction.transaction_type == t_upper)

        return query.order_by(Transaction.created_at.desc(), Transaction.id.desc()).offset(offset).limit(limit).all()

    def get_summary_stats(self) -> Dict[str, Any]:
        """Aggregate totals and counts by transaction type."""
        rows = (
            self.db.query(
                Transaction.transaction_type,
                func.count(Transaction.id),
                func.sum(Transaction.amount),
            )
            .filter(Transaction.status == "SUCCESS")
            .group_by(Transaction.transaction_type)
            .all()
        )
        stats = {
            "deposits_count": 0,
            "deposits_sum": Decimal("0.00"),
            "withdrawals_count": 0,
            "withdrawals_sum": Decimal("0.00"),
            "transfers_count": 0,
            "transfers_sum": Decimal("0.00"),
        }
        for t_type, count, total in rows:
            amount = total if total is not None else Decimal("0.00")
            if t_type == "DEPOSIT":
                stats["deposits_count"] += count
                stats["deposits_sum"] += amount
            elif t_type == "WITHDRAWAL":
                stats["withdrawals_count"] += count
                stats["withdrawals_sum"] += amount
            elif t_type in ("TRANSFER", "TRANSFER_OUT"):
                # Count logical transfers once (TRANSFER or TRANSFER_OUT leg)
                stats["transfers_count"] += count
                stats["transfers_sum"] += amount

        return stats
