from datetime import date

from pydantic import BaseModel


class CountByKeyResponse(BaseModel):
    key: str
    count: int


class ReportDynamicsPointResponse(BaseModel):
    period_start: date
    count: int


class AdminAnalyticsOverviewResponse(BaseModel):
    total_reports: int
    anonymous_reports: int
    open_reports: int
    anonymous_share: float
    open_share: float
    avg_hours_to_close: float | None
    by_category: list[CountByKeyResponse]
    by_zone: list[CountByKeyResponse]
    by_status: list[CountByKeyResponse]


class AdminAnalyticsDynamicsResponse(BaseModel):
    granularity: str
    points: list[ReportDynamicsPointResponse]
