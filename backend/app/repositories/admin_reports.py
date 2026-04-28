from datetime import datetime

from sqlalchemy import Select, false, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


def _apply_report_filters(
    statement: Select,
    *,
    public_number: str | None,
    category: str | None,
    zone: str | None,
    status: object | None,
    submit_mode: object | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> Select:
    if public_number:
        statement = statement.where(Report.public_number.ilike(f"%{public_number.strip()}%"))
    if category:
        statement = statement.where(Report.category == category)
    if zone:
        statement = statement.where(Report.zone == zone)
    if status:
        statement = statement.where(Report.status == status)
    if submit_mode:
        statement = statement.where(Report.submit_mode == submit_mode)
    if created_from:
        statement = statement.where(Report.created_at >= created_from)
    if created_to:
        statement = statement.where(Report.created_at <= created_to)
    return statement


async def count_reports(
    session: AsyncSession,
    *,
    is_admin: bool,
    resolver_zone: str | None,
    public_number: str | None = None,
    category: str | None = None,
    zone: str | None = None,
    status: object | None = None,
    submit_mode: object | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> int:
    statement = select(func.count(Report.id))
    statement = _apply_access_scope(statement, is_admin=is_admin, resolver_zone=resolver_zone)
    statement = _apply_report_filters(
        statement,
        public_number=public_number,
        category=category,
        zone=zone,
        status=status,
        submit_mode=submit_mode,
        created_from=created_from,
        created_to=created_to,
    )
    result = await session.scalar(statement)
    return int(result or 0)


async def list_reports(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    is_admin: bool,
    resolver_zone: str | None,
    public_number: str | None = None,
    category: str | None = None,
    zone: str | None = None,
    status: object | None = None,
    submit_mode: object | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> list[Report]:
    offset = (page - 1) * page_size
    statement = select(Report).options(selectinload(Report.author))
    statement = _apply_access_scope(statement, is_admin=is_admin, resolver_zone=resolver_zone)
    statement = _apply_report_filters(
        statement,
        public_number=public_number,
        category=category,
        zone=zone,
        status=status,
        submit_mode=submit_mode,
        created_from=created_from,
        created_to=created_to,
    )
    statement = statement.order_by(Report.created_at.desc(), Report.id.desc()).offset(offset).limit(page_size)
    result = await session.scalars(statement)
    return list(result.all())


async def get_report_by_id(
    session: AsyncSession,
    *,
    report_id: int,
    is_admin: bool,
    resolver_zone: str | None,
) -> Report | None:
    statement = (
        select(Report)
        .where(Report.id == report_id)
        .options(selectinload(Report.author), selectinload(Report.attachments))
    )
    statement = _apply_access_scope(statement, is_admin=is_admin, resolver_zone=resolver_zone)
    return await session.scalar(statement.limit(1))
