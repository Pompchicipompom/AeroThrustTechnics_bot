from datetime import date, datetime

from sqlalchemy import Select, false, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report


def _apply_access_scope(
    statement: Select,
    *,
    is_admin: bool,
    resolver_zone: str | None,
) -> Select:
    if is_admin:
        return statement
    if not resolver_zone:
        return statement.where(false())
    return statement.where(Report.zone == resolver_zone)


def _apply_created_range(
    statement: Select,
    *,
    created_from: datetime | None,
    created_to: datetime | None,
) -> Select:
    if created_from:
        statement = statement.where(Report.created_at >= created_from)
    if created_to:
        statement = statement.where(Report.created_at <= created_to)
    return statement


async def get_total_reports(
    session: AsyncSession,
    *,
    is_admin: bool,
    resolver_zone: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> int:
    statement = select(func.count(Report.id))
    statement = _apply_access_scope(statement, is_admin=is_admin, resolver_zone=resolver_zone)
    statement = _apply_created_range(statement, created_from=created_from, created_to=created_to)
    value = await session.scalar(statement)
    return int(value or 0)


async def get_submit_mode_counts(
    session: AsyncSession,
    *,
    is_admin: bool,
    resolver_zone: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> dict[str, int]:
    statement = select(Report.submit_mode, func.count(Report.id)).group_by(Report.submit_mode)
    statement = _apply_access_scope(statement, is_admin=is_admin, resolver_zone=resolver_zone)
    statement = _apply_created_range(statement, created_from=created_from, created_to=created_to)
    result = await session.execute(statement)
    return {str(mode): int(count) for mode, count in result.all()}


async def get_grouped_counts(
    session: AsyncSession,
    *,
    field: str,
    is_admin: bool,
    resolver_zone: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> list[tuple[str, int]]:
    column = getattr(Report, field)
    statement = select(column, func.count(Report.id)).group_by(column)
    statement = _apply_access_scope(statement, is_admin=is_admin, resolver_zone=resolver_zone)
    statement = _apply_created_range(statement, created_from=created_from, created_to=created_to)
    result = await session.execute(statement)
    rows: list[tuple[str, int]] = []
    for key, count in result.all():
        rows.append((str(key), int(count)))
    return rows


async def get_avg_hours_to_close(
    session: AsyncSession,
    *,
    is_admin: bool,
    resolver_zone: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> float | None:
    hours_expr = func.extract("epoch", Report.closed_at - Report.created_at) / 3600
    statement = select(func.avg(hours_expr)).where(Report.closed_at.is_not(None))
    statement = _apply_access_scope(statement, is_admin=is_admin, resolver_zone=resolver_zone)
    statement = _apply_created_range(statement, created_from=created_from, created_to=created_to)
    value = await session.scalar(statement)
    if value is None:
        return None
    return float(value)


async def get_dynamics(
    session: AsyncSession,
    *,
    granularity: str,
    is_admin: bool,
    resolver_zone: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> list[tuple[date, int]]:
    period_expr = func.date_trunc(granularity, Report.created_at)
    statement = (
        select(period_expr.label("period_start"), func.count(Report.id))
        .group_by(period_expr)
        .order_by(period_expr.asc())
    )
    statement = _apply_access_scope(statement, is_admin=is_admin, resolver_zone=resolver_zone)
    statement = _apply_created_range(statement, created_from=created_from, created_to=created_to)
    result = await session.execute(statement)
    rows: list[tuple[date, int]] = []
    for period_start, count in result.all():
        rows.append((period_start.date(), int(count)))
    return rows
