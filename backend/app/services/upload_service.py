import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from aiogram import Bot

from app.core.config import get_settings


class AttachmentValidationError(ValueError):
    """Attachment is invalid for MVP constraints."""


@dataclass(slots=True)
class DraftAttachment:
    temp_file_path: str
    original_file_name: str
    file_type: str
    file_size: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "temp_file_path": self.temp_file_path,
            "original_file_name": self.original_file_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int]) -> "DraftAttachment":
        return cls(
            temp_file_path=str(data["temp_file_path"]),
            original_file_name=str(data["original_file_name"]),
            file_type=str(data["file_type"]),
            file_size=int(data["file_size"]),
        )


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned[:120] if cleaned else "file"


def _get_upload_root() -> Path:
    settings = get_settings()
    root = Path(settings.uploads_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _ensure_within_root(path: Path, root: Path) -> None:
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise AttachmentValidationError("Невалидный путь сохранения вложения.")


def _validate_size(file_size: int | None) -> None:
    if file_size is None:
        return
    settings = get_settings()
    if file_size > settings.max_attachment_size_bytes:
        raise AttachmentValidationError(
            f"Файл превышает лимит {settings.max_attachment_size_mb} МБ."
        )


def _validate_document_type(file_name: str, mime_type: str | None) -> None:
    settings = get_settings()
    extension = Path(file_name).suffix.lower()
    mime = (mime_type or "").lower()
    extension_allowed = extension in settings.allowed_document_extensions_set
    mime_allowed = mime in settings.allowed_document_mime_types_set if mime else False

    if not extension_allowed and not mime_allowed:
        raise AttachmentValidationError("Этот тип файла пока не поддерживается.")


async def save_telegram_file_to_temp(
    *,
    bot: Bot,
    file_id: str,
    suggested_file_name: str,
    file_type: str,
    file_size: int | None,
) -> DraftAttachment:
    _validate_size(file_size)

    upload_root = _get_upload_root()
    temp_dir = (upload_root / "tmp").resolve()
    _ensure_within_root(temp_dir, upload_root)
    temp_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize_filename(suggested_file_name)
    temp_filename = f"{uuid4().hex}_{safe_name}"
    destination = (temp_dir / temp_filename).resolve()
    _ensure_within_root(destination, upload_root)

    telegram_file = await bot.get_file(file_id)
    await bot.download_file(telegram_file.file_path, destination=destination)

    real_size = destination.stat().st_size
    _validate_size(real_size)

    return DraftAttachment(
        temp_file_path=str(destination),
        original_file_name=safe_name,
        file_type=file_type,
        file_size=real_size,
    )


def validate_document_payload(file_name: str, mime_type: str | None, file_size: int | None) -> None:
    _validate_size(file_size)
    _validate_document_type(file_name=file_name, mime_type=mime_type)


def load_draft_attachments(raw_attachments: list[dict[str, str | int]]) -> list[DraftAttachment]:
    return [DraftAttachment.from_dict(item) for item in raw_attachments]


def cleanup_draft_attachments(drafts: list[DraftAttachment]) -> None:
    upload_root = _get_upload_root()
    for draft in drafts:
        path = Path(draft.temp_file_path)
        if not path.exists():
            continue
        try:
            _ensure_within_root(path, upload_root)
            path.unlink(missing_ok=True)
        except Exception:
            continue


def move_draft_to_report_dir(
    draft: DraftAttachment,
    public_number: str,
    index: int,
) -> tuple[str, str]:
    upload_root = _get_upload_root()
    report_dir = (upload_root / "reports" / public_number).resolve()
    _ensure_within_root(report_dir, upload_root)
    report_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(draft.temp_file_path).resolve()
    _ensure_within_root(source_path, upload_root)
    if not source_path.exists():
        raise FileNotFoundError(f"Временный файл не найден: {source_path}")

    original_safe = _sanitize_filename(draft.original_file_name)
    final_name = f"{index:02d}_{original_safe}"
    final_path = (report_dir / final_name).resolve()
    _ensure_within_root(final_path, upload_root)

    if final_path.exists():
        final_name = f"{index:02d}_{uuid4().hex[:8]}_{original_safe}"
        final_path = (report_dir / final_name).resolve()
        _ensure_within_root(final_path, upload_root)

    source_path.replace(final_path)
    relative_path = final_path.relative_to(upload_root).as_posix()
    return final_name, relative_path
