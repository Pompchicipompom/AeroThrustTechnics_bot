from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user import User
from app.services.user_reports_service import get_user_report_detail, list_user_reports


@pytest.mark.asyncio
async def test_list_user_reports_returns_only_own_reports(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_data: dict,
) -> None:
    async with session_factory() as session:
        open_author = await session.scalar(
            select(User).where(User.telegram_username == "open_author").limit(1),
        )
        assert open_author is not None

        reports = await list_user_reports(
            session,
            user_id=open_author.id,
            limit=20,
        )

    report_ids = [report.id for report in reports]
    assert report_ids == [5, 4, 3, 1]


@pytest.mark.asyncio
async def test_get_user_report_detail_denies_foreign_report_access(
    session_factory: async_sessionmaker[AsyncSession],
    seeded_data: dict,
) -> None:
    async with session_factory() as session:
        open_author = await session.scalar(
            select(User).where(User.telegram_username == "open_author").limit(1),
        )
        assert open_author is not None

        own_report = await get_user_report_detail(
            session,
            user_id=open_author.id,
            report_id=1,
        )
        foreign_report = await get_user_report_detail(
            session,
            user_id=open_author.id,
            report_id=2,
        )

    assert own_report is not None
    assert own_report.public_number == "AERO-0001"
    assert len(own_report.attachments) == 1
    assert foreign_report is None

