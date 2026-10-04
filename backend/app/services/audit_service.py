from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository
from app.core.logging import logger


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditLogRepository(db)

    def log(
        self,
        action: str,
        entity_type: str,
        description: str,
        actor_user_id: Optional[int] = None,
        entity_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        try:
            entry = AuditLog(
                actor_user_id=actor_user_id,
                action=action.upper(),
                entity_type=entity_type.upper(),
                entity_id=str(entity_id) if entity_id is not None else None,
                description=description,
                ip_address=ip_address,
            )
            created = self.repo.create(entry)
            logger.info(f"AUDIT [{entry.action}] {entry.description} (actor={actor_user_id}, ip={ip_address})")
            return created
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            return None
