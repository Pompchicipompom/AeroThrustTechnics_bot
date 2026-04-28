from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report


async def create_report(session: AsyncSession, report: Report) -> Report:
    session.add(report)
    await session.flush()
    return report
