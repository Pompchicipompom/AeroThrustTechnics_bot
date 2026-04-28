from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.admin_auth import get_current_admin
from app.db.session import get_db_session
from app.models.admin_user import AdminUser
from app.schemas.admin_analytics import (
    AdminAnalyticsDynamicsResponse,
    AdminAnalyticsOverviewResponse,
    CountByKeyResponse,
    ReportDynamicsPointResponse,
)
from app.services.admin_analytics_service import build_dynamics, build_overview

router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"])


@router.get("/overview", response_model=AdminAnalyticsOverviewResponse)
async def admin_analytics_overview(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AdminAnalyticsOverviewResponse:
    overview = await build_overview(
        session,
        current_admin=current_admin,
        created_from=created_from,
        created_to=created_to,
    )
    return AdminAnalyticsOverviewResponse(
        total_reports=overview.total_reports,
        anonymous_reports=overview.anonymous_reports,
        open_reports=overview.open_reports,
        anonymous_share=overview.anonymous_share,
        open_share=overview.open_share,
        avg_hours_to_close=overview.avg_hours_to_close,
        by_category=[CountByKeyResponse(key=key, count=count) for key, count in overview.by_category],
        by_zone=[CountByKeyResponse(key=key, count=count) for key, count in overview.by_zone],
        by_status=[CountByKeyResponse(key=key, count=count) for key, count in overview.by_status],
    )


@router.get("/dynamics", response_model=AdminAnalyticsDynamicsResponse)
async def admin_analytics_dynamics(
    granularity: Literal["day", "week"] = Query(default="day"),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AdminAnalyticsDynamicsResponse:
    try:
        points = await build_dynamics(
            session,
            current_admin=current_admin,
            granularity=granularity,
            created_from=created_from,
            created_to=created_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AdminAnalyticsDynamicsResponse(
        granularity=granularity,
        points=[ReportDynamicsPointResponse(period_start=period_start, count=count) for period_start, count in points],
    )
