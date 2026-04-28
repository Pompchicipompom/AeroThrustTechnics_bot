from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ReportStatus, SubmitMode


class ReportAuthorResponse(BaseModel):
    technical_id: int
    display_name: str | None
    telegram_username: str | None


class ReportAttachmentResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_path: str
    file_size: int
    created_at: datetime


class ReportListItemResponse(BaseModel):
    id: int
    public_number: str
    submit_mode: SubmitMode
    category: str
    zone: str
    status: ReportStatus
    text_preview: str
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    author: ReportAuthorResponse | None


class PageMetaResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ReportListResponse(BaseModel):
    items: list[ReportListItemResponse]
    page: PageMetaResponse


class ReportDetailResponse(BaseModel):
    id: int
    public_number: str
    submit_mode: SubmitMode
    category: str
    zone: str
    status: ReportStatus
    text: str
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    author: ReportAuthorResponse | None
    attachments: list[ReportAttachmentResponse]


class ReportStatusUpdateRequest(BaseModel):
    status: ReportStatus = Field(description="New report status.")


class ReportStatusUpdateResponse(BaseModel):
    id: int
    public_number: str
    status: ReportStatus
    updated_at: datetime
    closed_at: datetime | None
