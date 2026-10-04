from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    logId: Optional[int] = None
    actorUserId: Optional[int] = None
    actorId: Optional[int] = None
    actorName: Optional[str] = None
    action: str
    entityType: str
    entityId: Optional[str] = None
    description: str
    details: Optional[str] = None
    ipAddress: Optional[str] = None
    timestamp: datetime
    createdAt: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)

    def __init__(self, **data):
        if "logId" not in data and "id" in data:
            data["logId"] = data["id"]
        if "actorId" not in data and "actorUserId" in data:
            data["actorId"] = data["actorUserId"]
        if "details" not in data and "description" in data:
            data["details"] = data["description"]
        if "createdAt" not in data and "timestamp" in data:
            data["createdAt"] = data["timestamp"]
        super().__init__(**data)
