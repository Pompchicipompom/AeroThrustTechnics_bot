from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.admin_auth import get_current_admin
from app.db.session import get_db_session
from app.models.admin_user import AdminUser
from app.schemas.admin_audit import AuditLogItemResponse, AuditLogListResponse
from app.schemas.admin_reports import PageMetaResponse
from app.services.admin_audit_service import get_audit_logs_page

router = APIRouter(prefix="/admin/audit-logs", tags=["admin-audit"])


@router.get("", response_model=AuditLogListResponse)
async def admin_list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AuditLogListResponse:
    result = await get_audit_logs_page(
        session,
        current_admin=current_admin,
        page=page,
        page_size=page_size,
        action=action,
        entity_type=entity_type,
        created_from=created_from,
        created_to=created_to,
    )

    return AuditLogListResponse(
        items=[
            AuditLogItemResponse(
                id=log.id,
                admin_user_id=log.admin_user_id,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                action=log.action,
                payload_json=log.payload_json,
                created_at=log.created_at,
            )
            for log in result.items
        ],
        page=PageMetaResponse(
            page=result.page,
            page_size=result.page_size,
            total_items=result.total_items,
            total_pages=result.total_pages,
        ),
    )
