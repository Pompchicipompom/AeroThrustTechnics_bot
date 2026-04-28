from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.models.attachment import Attachment
from app.models.enums import SubmitMode
from app.models.user import User
from app.services.report_service import ReportDraft, create_report_from_draft
from app.services.upload_service import DraftAttachment


def _prepare_temp_draft_file(*, file_name: str, content: bytes) -> DraftAttachment:
    upload_root = Path(get_settings().uploads_root).resolve()
    temp_dir = upload_root / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_path = temp_dir / f"{uuid4().hex}_{file_name}"
    temp_path.write_bytes(content)
    return DraftAttachment(
        temp_file_path=str(temp_path),
        original_file_name=file_name,
        file_type="image/jpeg" if file_name.endswith(".jpg") else "application/pdf",
        file_size=temp_path.stat().st_size,
    )


@pytest.mark.asyncio
async def test_report_attachments_saved_and_available_in_admin_api(
    client: AsyncClient,
    seeded_data: dict,
    auth_headers,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    drafts = [
        _prepare_temp_draft_file(file_name="photo1.jpg", content=b"photo-1"),
        _prepare_temp_draft_file(file_name="doc1.pdf", content=b"doc-1"),
        _prepare_temp_draft_file(file_name="photo2.jpg", content=b"photo-2"),
    ]

    async with session_factory() as session:
        author = User(
            telegram_id=900000001,
            telegram_username="attach_user",
            telegram_first_name="Attach",
            telegram_last_name="Tester",
            is_authorized=True,
        )
        session.add(author)
        await session.flush()

        created = await create_report_from_draft(
            session,
            author=author,
            draft=ReportDraft(
                submit_mode=SubmitMode.OPEN,
                category="process",
                text="Attachment persistence check",
                attachments=drafts,
            ),
        )

    detail_response = await client.get(f"/admin/reports/{created.report_id}", headers=headers)
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert len(detail_payload["attachments"]) == 3

    for attachment in detail_payload["attachments"]:
        file_response = await client.get(
            f"/admin/reports/{created.report_id}/attachments/{attachment['id']}/file",
            headers=headers,
        )
        assert file_response.status_code == 200
        assert file_response.content


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path_transform",
    [
        lambda value: f"uploads/{value}",
        lambda value: value.replace("/", "\\"),
    ],
)
async def test_attachment_file_endpoint_supports_legacy_path_formats(
    client: AsyncClient,
    seeded_data: dict,
    auth_headers,
    session_factory: async_sessionmaker[AsyncSession],
    path_transform,
) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    draft = _prepare_temp_draft_file(file_name="legacy.jpg", content=b"legacy-photo")

    async with session_factory() as session:
        author = User(
            telegram_id=900000011,
            telegram_username="legacy_user",
            telegram_first_name="Legacy",
            telegram_last_name="Path",
            is_authorized=True,
        )
        session.add(author)
        await session.flush()

        created = await create_report_from_draft(
            session,
            author=author,
            draft=ReportDraft(
                submit_mode=SubmitMode.OPEN,
                category="process",
                text="Legacy path compatibility",
                attachments=[draft],
            ),
        )

    async with session_factory() as session:
        result = await session.execute(
            select(Attachment).where(Attachment.report_id == created.report_id).limit(1),
        )
        attachment = result.scalar_one_or_none()
        assert attachment is not None
        attachment.file_path = path_transform(attachment.file_path)
        await session.commit()
        attachment_id = attachment.id

    file_response = await client.get(
        f"/admin/reports/{created.report_id}/attachments/{attachment_id}/file",
        headers=headers,
    )
    assert file_response.status_code == 200
    assert file_response.content == b"legacy-photo"


@pytest.mark.asyncio
async def test_attachment_file_endpoint_fallbacks_to_report_dir_when_db_path_is_outdated(
    client: AsyncClient,
    seeded_data: dict,
    auth_headers,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    draft = _prepare_temp_draft_file(file_name="fallback.pdf", content=b"fallback-doc")

    async with session_factory() as session:
        author = User(
            telegram_id=900000021,
            telegram_username="fallback_user",
            telegram_first_name="Fallback",
            telegram_last_name="Path",
            is_authorized=True,
        )
        session.add(author)
        await session.flush()

        created = await create_report_from_draft(
            session,
            author=author,
            draft=ReportDraft(
                submit_mode=SubmitMode.OPEN,
                category="process",
                text="Fallback path compatibility",
                attachments=[draft],
            ),
        )

    async with session_factory() as session:
        result = await session.execute(
            select(Attachment).where(Attachment.report_id == created.report_id).limit(1),
        )
        attachment = result.scalar_one_or_none()
        assert attachment is not None
        attachment.file_path = "legacy/non-existing/location/fallback.pdf"
        await session.commit()
        attachment_id = attachment.id

    file_response = await client.get(
        f"/admin/reports/{created.report_id}/attachments/{attachment_id}/file",
        headers=headers,
    )
    assert file_response.status_code == 200
    assert file_response.content == b"fallback-doc"
