from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.reporting import CATEGORY_TO_ZONE
from app.models.attachment import Attachment
from app.models.enums import ReportStatus, SubmitMode
from app.models.report import Report
from app.models.user import User
from app.repositories.attachments import create_attachments
from app.repositories.reports import create_report
from app.services.upload_service import (
    DraftAttachment,
    cleanup_draft_attachments,
    move_draft_to_report_dir,
)


@dataclass(slots=True)
class ReportDraft:
    submit_mode: SubmitMode
    category: str
    text: str
    attachments: list[DraftAttachment]


@dataclass(slots=True)
class CreatedReport:
    report_id: int
    public_number: str
    attachments_count: int


def build_public_number(report_id: int, created_at: datetime) -> str:
    return f"AT-{created_at:%Y%m%d}-{report_id:06d}"


def _cleanup_final_files(relative_paths: list[str]) -> None:
    settings = get_settings()
    upload_root = Path(settings.uploads_root).resolve()
    for relative_path in relative_paths:
        path = (upload_root / relative_path).resolve()
        if path.exists() and path.is_relative_to(upload_root):
            path.unlink(missing_ok=True)


async def create_report_from_draft(
    session: AsyncSession,
    *,
    author: User,
    draft: ReportDraft,
) -> CreatedReport:
    if draft.category not in CATEGORY_TO_ZONE:
        raise ValueError("Неизвестная категория сообщения.")

    cleaned_text = draft.text.strip()
    if not cleaned_text:
        raise ValueError("Текст сообщения не может быть пустым.")

    created_at = datetime.now(tz=timezone.utc)
    report = Report(
        public_number=f"PENDING-{uuid4().hex}",
        submit_mode=draft.submit_mode,
        category=draft.category,
        zone=CATEGORY_TO_ZONE[draft.category],
        status=ReportStatus.NEW,
        text=cleaned_text,
        author_user_id=author.id,
        created_at=created_at,
        updated_at=created_at,
    )
    await create_report(session, report)

    public_number = build_public_number(report.id, created_at)
    report.public_number = public_number

    created_attachments: list[Attachment] = []
    final_relative_paths: list[str] = []
    try:
        for index, draft_attachment in enumerate(draft.attachments, start=1):
            final_name, relative_path = move_draft_to_report_dir(
                draft=draft_attachment,
                public_number=public_number,
                index=index,
            )
            final_relative_paths.append(relative_path)
            created_attachments.append(
                Attachment(
                    report_id=report.id,
                    file_name=final_name,
                    file_type=draft_attachment.file_type,
                    file_path=relative_path,
                    file_size=draft_attachment.file_size,
                )
            )

        if created_attachments:
            await create_attachments(session, created_attachments)

        await session.commit()
    except Exception:
        await session.rollback()
        _cleanup_final_files(final_relative_paths)
        raise
    finally:
        cleanup_draft_attachments(draft.attachments)

    return CreatedReport(
        report_id=report.id,
        public_number=public_number,
        attachments_count=len(created_attachments),
    )
