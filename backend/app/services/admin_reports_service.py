from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.models.enums import AdminRole, ReportStatus, SubmitMode
from app.models.report import Report
from app.repositories.admin_reports import count_reports, get_report_by_id, list_reports
from app.services.audit_service import log_admin_action


@dataclass(slots=True, frozen=True)
class ReportsPage:
    items: list[Report]
    total_items: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.total_items == 0:
            return 0
        return (self.total_items + self.page_size - 1) // self.page_size


@dataclass(slots=True, frozen=True)
class ReportFilters:
    page: int
    page_size: int
    public_number: str | None = None
    category: str | None = None
    zone: str | None = None
    status: ReportStatus | None = None
    submit_mode: SubmitMode | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


def _is_admin(user: AdminUser) -> bool:
    return user.role == AdminRole.ADMIN


def _ensure_resolver_zone_scope(user: AdminUser, requested_zone: str | None) -> None:
    if _is_admin(user):
        return
    if requested_zone is not None and requested_zone != user.zone:
        raise PermissionError("Resolver can only access reports in own zone.")


async def get_reports_page(
    session: AsyncSession,
    *,
    current_admin: AdminUser,
    filters: ReportFilters,
) -> ReportsPage:
    _ensure_resolver_zone_scope(current_admin, filters.zone)
    is_admin = _is_admin(current_admin)
    total = await count_reports(
        session,
        is_admin=is_admin,
        resolver_zone=current_admin.zone,
        public_number=filters.public_number,
        category=filters.category,
        zone=filters.zone,
        status=filters.status,
        submit_mode=filters.submit_mode,
        created_from=filters.created_from,
        created_to=filters.created_to,
    )
    items = await list_reports(
        session,
        page=filters.page,
        page_size=filters.page_size,
        is_admin=is_admin,
        resolver_zone=current_admin.zone,
        public_number=filters.public_number,
        category=filters.category,
        zone=filters.zone,
        status=filters.status,
        submit_mode=filters.submit_mode,
        created_from=filters.created_from,
        created_to=filters.created_to,
    )
    return ReportsPage(items=items, total_items=total, page=filters.page, page_size=filters.page_size)


async def get_report_or_404(
    session: AsyncSession,
    *,
    current_admin: AdminUser,
    report_id: int,
) -> Report | None:
    report = await get_report_by_id(
        session,
        report_id=report_id,
        is_admin=_is_admin(current_admin),
        resolver_zone=current_admin.zone,
    )
    return report


async def log_report_view(
    session: AsyncSession,
    *,
    current_admin: AdminUser,
    report: Report,
) -> None:
    await log_admin_action(
        session,
        admin_user_id=current_admin.id,
        entity_type="report",
        entity_id=report.id,
        action="report_viewed",
        payload_json={
            "zone": report.zone,
            "public_number": report.public_number,
        },
    )
    await session.commit()


async def update_report_status(
    session: AsyncSession,
    *,
    current_admin: AdminUser,
    report: Report,
    new_status: ReportStatus,
) -> Report:
    previous_status = report.status
    if previous_status == new_status:
        return report

    now = datetime.now(tz=UTC)
    report.status = new_status
    report.updated_at = now
    if new_status == ReportStatus.CLOSED:
        report.closed_at = now
    elif report.closed_at is not None:
        report.closed_at = None

    await log_admin_action(
        session,
        admin_user_id=current_admin.id,
        entity_type="report",
        entity_id=report.id,
        action="status_changed",
        payload_json={
            "from_status": previous_status.value,
            "to_status": new_status.value,
            "zone": report.zone,
            "public_number": report.public_number,
        },
    )
    await session.commit()
    await session.refresh(report)
    return report
