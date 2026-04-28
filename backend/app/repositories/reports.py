from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report import Report


async def create_report(session: AsyncSession, report: Report) -> Report:
    session.add(report)
    await session.flush()
    return report


async def list_reports_by_author(
    session: AsyncSession,
    *,
    author_user_id: int,
    limit: int = 20,
) -> list[Report]:
    statement = (
        select(Report)
        .where(Report.author_user_id == author_user_id)
        .order_by(Report.created_at.desc(), Report.id.desc())
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result.all())


async def get_report_by_id_and_author(
    session: AsyncSession,
    *,
    report_id: int,
    author_user_id: int,
) -> Report | None:
    statement = (
        select(Report)
        .where(
            Report.id == report_id,
            Report.author_user_id == author_user_id,
        )
        .options(selectinload(Report.attachments))
        .limit(1)
    )
    return await session.scalar(statement)
