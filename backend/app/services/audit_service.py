from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_logs import create_audit_log


async def log_admin_action(
    session: AsyncSession,
    *,
    admin_user_id: int,
    entity_type: str,
    entity_id: int,
    action: str,
    payload_json: dict[str, Any] | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        admin_user_id=admin_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        payload_json=payload_json,
    )
    return await create_audit_log(session, audit_log)
