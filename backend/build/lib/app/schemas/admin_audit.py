from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.admin_reports import PageMetaResponse


class AuditLogItemResponse(BaseModel):
    id: int
    admin_user_id: int | None
    entity_type: str
    entity_id: int
    action: str
    payload_json: dict[str, Any] | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItemResponse]
    page: PageMetaResponse
