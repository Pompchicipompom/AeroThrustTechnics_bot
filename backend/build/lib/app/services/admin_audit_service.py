from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.models.enums import AdminRole
from app.models.audit_log import AuditLog
from app.repositories.audit_logs import count_audit_logs, list_audit_logs


@dataclass(slots=True, frozen=True)
class AuditLogsPage:
    items: list[AuditLog]
    total_items: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.total_items == 0:
            return 0
        return (self.total_items + self.page_size - 1) // self.page_size


async def get_audit_logs_page(
    session: AsyncSession,
    *,
    current_admin: AdminUser,
    page: int,
    page_size: int,
    action: str | None,
    entity_type: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> AuditLogsPage:
    scoped_admin_user_id: int | None = None
    if current_admin.role == AdminRole.RESOLVER:
        scoped_admin_user_id = current_admin.id

    total = await count_audit_logs(
        session,
        admin_user_id=scoped_admin_user_id,
        action=action,
        entity_type=entity_type,
        created_from=created_from,
        created_to=created_to,
    )
    items = await list_audit_logs(
        session,
        page=page,
        page_size=page_size,
        admin_user_id=scoped_admin_user_id,
        action=action,
        entity_type=entity_type,
        created_from=created_from,
        created_to=created_to,
    )
    return AuditLogsPage(items=items, total_items=total, page=page, page_size=page_size)
