from typing import Optional, List
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload
from app.models.audit_log import AuditLog
from app.models.user import User


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, log: AuditLog) -> AuditLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list_all(
        self,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        query = self.db.query(AuditLog).options(joinedload(AuditLog.actor))
        if action:
            query = query.filter(AuditLog.action == action.upper())
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type.upper())
        if search:
            needle = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(AuditLog.description).like(needle),
                    AuditLog.entity_id.like(needle),
                )
            )

        return query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).offset(offset).limit(limit).all()
