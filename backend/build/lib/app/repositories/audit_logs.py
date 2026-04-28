from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def create_audit_log(session: AsyncSession, audit_log: AuditLog) -> AuditLog:
    session.add(audit_log)
    await session.flush()
    return audit_log


def _apply_filters(
    statement: Select[tuple[AuditLog]],
    *,
    admin_user_id: int | None,
    action: str | None,
    entity_type: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> Select[tuple[AuditLog]]:
    if admin_user_id is not None:
        statement = statement.where(AuditLog.admin_user_id == admin_user_id)
    if action is not None:
        statement = statement.where(AuditLog.action == action)
    if entity_type is not None:
        statement = statement.where(AuditLog.entity_type == entity_type)
    if created_from is not None:
        statement = statement.where(AuditLog.created_at >= created_from)
    if created_to is not None:
        statement = statement.where(AuditLog.created_at <= created_to)
    return statement


async def count_audit_logs(
    session: AsyncSession,
    *,
    admin_user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> int:
    statement = _apply_filters(
        select(func.count(AuditLog.id)),
        admin_user_id=admin_user_id,
        action=action,
        entity_type=entity_type,
        created_from=created_from,
        created_to=created_to,
    )
    result = await session.scalar(statement)
    return int(result or 0)


async def list_audit_logs(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    admin_user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> list[AuditLog]:
    offset = (page - 1) * page_size
    statement = _apply_filters(
        select(AuditLog),
        admin_user_id=admin_user_id,
        action=action,
        entity_type=entity_type,
        created_from=created_from,
        created_to=created_to,
    )
    statement = statement.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset(offset).limit(page_size)
    result = await session.scalars(statement)
    return list(result.all())
