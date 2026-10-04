from typing import List
from sqlalchemy.orm import Session
from app.models.email_log import EmailLog


class EmailLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, log: EmailLog) -> EmailLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list_all(self, limit: int = 100, offset: int = 0) -> List[EmailLog]:
        return (
            self.db.query(EmailLog)
            .order_by(EmailLog.created_at.desc(), EmailLog.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
