from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.repositories.reports import get_report_by_id_and_author, list_reports_by_author


async def list_user_reports(
    session: AsyncSession,
    *,
    user_id: int,
    limit: int = 20,
) -> list[Report]:
    return await list_reports_by_author(
        session,
        author_user_id=user_id,
        limit=limit,
    )


async def get_user_report_detail(
    session: AsyncSession,
    *,
    user_id: int,
    report_id: int,
) -> Report | None:
    return await get_report_by_id_and_author(
        session,
        report_id=report_id,
        author_user_id=user_id,
    )

