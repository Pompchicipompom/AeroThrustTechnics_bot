from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.admin_auth import get_current_admin
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.admin_user import AdminUser
from app.models.enums import ReportStatus, SubmitMode
from app.models.report import Report
from app.schemas.admin_reports import (
    PageMetaResponse,
    ReportAttachmentResponse,
    ReportAuthorResponse,
    ReportDetailResponse,
    ReportListItemResponse,
    ReportListResponse,
    ReportStatusUpdateRequest,
    ReportStatusUpdateResponse,
)
from app.services.admin_reports_service import (
    ReportFilters,
    get_report_or_404,
    get_reports_page,
    log_report_view,
    update_report_status,
)

router = APIRouter(prefix="/admin/reports", tags=["admin-reports"])


def _build_display_name(report: Report) -> str | None:
    if report.author is None:
        return None

    if report.author.telegram_first_name or report.author.telegram_last_name:
        full_name = f"{report.author.telegram_first_name or ''} {report.author.telegram_last_name or ''}".strip()
        if full_name:
            return full_name

    if report.author.telegram_username:
        return f"@{report.author.telegram_username}"

    return f"User {report.author.id}"


def _build_author(report: Report) -> ReportAuthorResponse | None:
    if report.submit_mode == SubmitMode.ANONYMOUS:
        return None
    if report.author is None:
        return None
    return ReportAuthorResponse(
        technical_id=report.author.id,
        display_name=_build_display_name(report),
        telegram_username=report.author.telegram_username,
    )


def _build_list_item(report: Report) -> ReportListItemResponse:
    return ReportListItemResponse(
        id=report.id,
        public_number=report.public_number,
        submit_mode=report.submit_mode,
        category=report.category,
        zone=report.zone,
        status=report.status,
        text_preview=report.text[:200],
        created_at=report.created_at,
        updated_at=report.updated_at,
        closed_at=report.closed_at,
        author=_build_author(report),
    )


def _build_detail(report: Report) -> ReportDetailResponse:
    attachments = sorted(report.attachments, key=lambda item: item.id)
    return ReportDetailResponse(
        id=report.id,
        public_number=report.public_number,
        submit_mode=report.submit_mode,
        category=report.category,
        zone=report.zone,
        status=report.status,
        text=report.text,
        created_at=report.created_at,
        updated_at=report.updated_at,
        closed_at=report.closed_at,
        author=_build_author(report),
        attachments=[
            ReportAttachmentResponse(
                id=attachment.id,
                file_name=attachment.file_name,
                file_type=attachment.file_type,
                file_path=attachment.file_path,
                file_size=attachment.file_size,
                created_at=attachment.created_at,
            )
            for attachment in attachments
        ],
    )


def _normalize_attachment_path(raw_path: str) -> str:
    normalized = raw_path.strip().replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized


def _iter_attachment_candidates(*, stored_path: str, upload_root: Path, fallback_path: str | None) -> list[Path]:
    normalized = _normalize_attachment_path(stored_path)
    candidates: list[Path] = []

    # 1) Canonical case: relative path in DB, e.g. reports/AT-.../01_file.pdf
    if normalized:
        candidates.append(upload_root / normalized.lstrip("/"))

        # 2) Backward compatibility: DB path may already start with "uploads/".
        if normalized.startswith("uploads/"):
            candidates.append(upload_root / normalized.removeprefix("uploads/"))

        # 3) Backward compatibility: DB path may accidentally store absolute prefix.
        marker = "/uploads/"
        if marker in normalized:
            suffix = normalized.split(marker, maxsplit=1)[1]
            if suffix:
                candidates.append(upload_root / suffix.lstrip("/"))

        # 4) Absolute path (works when it still points under UPLOADS_ROOT).
        path_object = Path(normalized)
        if path_object.is_absolute():
            candidates.append(path_object)

    # 5) Final fallback based on report number + file name.
    if fallback_path:
        candidates.append(upload_root / fallback_path)

    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _resolve_attachment_path(stored_path: str, *, fallback_path: str | None = None) -> Path:
    upload_root = Path(get_settings().uploads_root).resolve()
    candidates = _iter_attachment_candidates(
        stored_path=stored_path,
        upload_root=upload_root,
        fallback_path=fallback_path,
    )

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue

        if not resolved.is_relative_to(upload_root):
            continue

        if resolved.exists() and resolved.is_file():
            return resolved

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file not found.")


@router.get("", response_model=ReportListResponse)
async def admin_list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    public_number: str | None = Query(default=None),
    category: str | None = Query(default=None),
    zone: str | None = Query(default=None),
    status_filter: ReportStatus | None = Query(default=None, alias="status"),
    submit_mode: SubmitMode | None = Query(default=None),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ReportListResponse:
    try:
        reports_page = await get_reports_page(
            session,
            current_admin=current_admin,
            filters=ReportFilters(
                page=page,
                page_size=page_size,
                public_number=public_number,
                category=category,
                zone=zone,
                status=status_filter,
                submit_mode=submit_mode,
                created_from=created_from,
                created_to=created_to,
            ),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return ReportListResponse(
        items=[_build_list_item(item) for item in reports_page.items],
        page=PageMetaResponse(
            page=reports_page.page,
            page_size=reports_page.page_size,
            total_items=reports_page.total_items,
            total_pages=reports_page.total_pages,
        ),
    )


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def admin_get_report(
    report_id: int,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ReportDetailResponse:
    report = await get_report_or_404(
        session,
        current_admin=current_admin,
        report_id=report_id,
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    await log_report_view(
        session,
        current_admin=current_admin,
        report=report,
    )
    return _build_detail(report)


@router.patch("/{report_id}/status", response_model=ReportStatusUpdateResponse)
async def admin_update_report_status(
    report_id: int,
    payload: ReportStatusUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ReportStatusUpdateResponse:
    report = await get_report_or_404(
        session,
        current_admin=current_admin,
        report_id=report_id,
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    updated_report = await update_report_status(
        session,
        current_admin=current_admin,
        report=report,
        new_status=payload.status,
    )
    return ReportStatusUpdateResponse(
        id=updated_report.id,
        public_number=updated_report.public_number,
        status=updated_report.status,
        updated_at=updated_report.updated_at,
        closed_at=updated_report.closed_at,
    )


@router.get("/{report_id}/attachments/{attachment_id}/file")
async def admin_get_attachment_file(
    report_id: int,
    attachment_id: int,
    download: bool = Query(default=False),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> FileResponse:
    report = await get_report_or_404(
        session,
        current_admin=current_admin,
        report_id=report_id,
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    attachment = next((item for item in report.attachments if item.id == attachment_id), None)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    fallback_path = f"reports/{report.public_number}/{attachment.file_name}"
    attachment_path = _resolve_attachment_path(
        attachment.file_path,
        fallback_path=fallback_path,
    )
    disposition = "attachment" if download else "inline"
    return FileResponse(
        path=str(attachment_path),
        media_type=attachment.file_type or "application/octet-stream",
        filename=attachment.file_name,
        content_disposition_type=disposition,
    )
