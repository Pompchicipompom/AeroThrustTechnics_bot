from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.models.enums import AdminRole
from app.repositories.admin_analytics import (
    get_avg_hours_to_close,
    get_dynamics,
    get_grouped_counts,
    get_submit_mode_counts,
    get_total_reports,
)


@dataclass(slots=True, frozen=True)
class AnalyticsOverview:
    total_reports: int
    anonymous_reports: int
    open_reports: int
    anonymous_share: float
    open_share: float
    avg_hours_to_close: float | None
    by_category: list[tuple[str, int]]
    by_zone: list[tuple[str, int]]
    by_status: list[tuple[str, int]]


def _is_admin(user: AdminUser) -> bool:
    return user.role == AdminRole.ADMIN


async def build_overview(
    session: AsyncSession,
    *,
    current_admin: AdminUser,
    created_from: datetime | None,
    created_to: datetime | None,
) -> AnalyticsOverview:
    is_admin = _is_admin(current_admin)
    resolver_zone = current_admin.zone
    total_reports = await get_total_reports(
        session,
        is_admin=is_admin,
        resolver_zone=resolver_zone,
        created_from=created_from,
        created_to=created_to,
    )
    submit_mode_counts = await get_submit_mode_counts(
        session,
        is_admin=is_admin,
        resolver_zone=resolver_zone,
        created_from=created_from,
        created_to=created_to,
    )
    anonymous_reports = submit_mode_counts.get("anonymous", 0)
    open_reports = submit_mode_counts.get("open", 0)
    if total_reports > 0:
        anonymous_share = anonymous_reports / total_reports
        open_share = open_reports / total_reports
    else:
        anonymous_share = 0.0
        open_share = 0.0

    avg_hours_to_close = await get_avg_hours_to_close(
        session,
        is_admin=is_admin,
        resolver_zone=resolver_zone,
        created_from=created_from,
        created_to=created_to,
    )

    by_category = await get_grouped_counts(
        session,
        field="category",
        is_admin=is_admin,
        resolver_zone=resolver_zone,
        created_from=created_from,
        created_to=created_to,
    )
    by_zone = await get_grouped_counts(
        session,
        field="zone",
        is_admin=is_admin,
        resolver_zone=resolver_zone,
        created_from=created_from,
        created_to=created_to,
    )
    by_status = await get_grouped_counts(
        session,
        field="status",
        is_admin=is_admin,
        resolver_zone=resolver_zone,
        created_from=created_from,
        created_to=created_to,
    )
    return AnalyticsOverview(
        total_reports=total_reports,
        anonymous_reports=anonymous_reports,
        open_reports=open_reports,
        anonymous_share=anonymous_share,
        open_share=open_share,
        avg_hours_to_close=avg_hours_to_close,
        by_category=by_category,
        by_zone=by_zone,
        by_status=by_status,
    )


async def build_dynamics(
    session: AsyncSession,
    *,
    current_admin: AdminUser,
    granularity: str,
    created_from: datetime | None,
    created_to: datetime | None,
) -> list[tuple[date, int]]:
    return await get_dynamics(
        session,
        granularity=granularity,
        is_admin=_is_admin(current_admin),
        resolver_zone=current_admin.zone,
        created_from=created_from,
        created_to=created_to,
    )
