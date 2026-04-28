import asyncio

import pytest

from app.bot.handlers.report_flow import (
    _ATTACHMENT_STATE_LOCKS,
    _append_attachment_to_state,
    _build_summary_text,
    _extract_attachments,
)
from app.models.enums import SubmitMode
from app.services.upload_service import DraftAttachment


class FakeFSMState:
    def __init__(self, delay: float = 0.0) -> None:
        self._data: dict[str, object] = {"attachments": []}
        self._delay = delay

    async def get_data(self) -> dict[str, object]:
        if self._delay:
            await asyncio.sleep(self._delay)
        return dict(self._data)

    async def update_data(self, **kwargs: object) -> None:
        if self._delay:
            await asyncio.sleep(self._delay)
        self._data.update(kwargs)


def _make_draft_attachment(name: str, file_type: str, size: int) -> DraftAttachment:
    return DraftAttachment(
        temp_file_path=f"/tmp/{name}",
        original_file_name=name,
        file_type=file_type,
        file_size=size,
    )


@pytest.mark.asyncio
async def test_attachment_counter_single_file() -> None:
    _ATTACHMENT_STATE_LOCKS.clear()
    state = FakeFSMState()
    count = await _append_attachment_to_state(
        state=state,
        user_id=1,
        draft_attachment=_make_draft_attachment("one.jpg", "image/jpeg", 100),
    )
    assert count == 1
    attachments = _extract_attachments(await state.get_data())
    assert len(attachments) == 1


@pytest.mark.asyncio
async def test_attachment_counter_sequential_three_files() -> None:
    _ATTACHMENT_STATE_LOCKS.clear()
    state = FakeFSMState()
    counts = []
    for idx in range(1, 4):
        count = await _append_attachment_to_state(
            state=state,
            user_id=2,
            draft_attachment=_make_draft_attachment(f"f{idx}.txt", "text/plain", idx),
        )
        counts.append(count)

    assert counts == [1, 2, 3]
    attachments = _extract_attachments(await state.get_data())
    assert len(attachments) == 3


@pytest.mark.asyncio
async def test_attachment_counter_concurrent_updates_no_loss() -> None:
    _ATTACHMENT_STATE_LOCKS.clear()
    state = FakeFSMState(delay=0.01)

    async def _append(idx: int) -> int:
        return await _append_attachment_to_state(
            state=state,
            user_id=3,
            draft_attachment=_make_draft_attachment(f"c{idx}.jpg", "image/jpeg", 10 + idx),
        )

    counts = await asyncio.gather(_append(1), _append(2), _append(3))
    assert sorted(counts) == [1, 2, 3]

    attachments = _extract_attachments(await state.get_data())
    assert len(attachments) == 3


@pytest.mark.asyncio
async def test_summary_uses_actual_attachments_count() -> None:
    _ATTACHMENT_STATE_LOCKS.clear()
    state = FakeFSMState()
    for idx in range(1, 4):
        await _append_attachment_to_state(
            state=state,
            user_id=4,
            draft_attachment=_make_draft_attachment(f"s{idx}.pdf", "application/pdf", 1000 + idx),
        )

    attachments = _extract_attachments(await state.get_data())
    summary = _build_summary_text(
        submit_mode=SubmitMode.OPEN,
        category="safety",
        text="Проверка summary",
        attachments_count=len(attachments),
    )
    assert "<b>Вложений:</b> 3" in summary


@pytest.mark.asyncio
async def test_mixed_photo_and_document_counted_correctly() -> None:
    _ATTACHMENT_STATE_LOCKS.clear()
    state = FakeFSMState()

    photo_count = await _append_attachment_to_state(
        state=state,
        user_id=5,
        draft_attachment=_make_draft_attachment("photo.jpg", "image/jpeg", 2048),
    )
    doc_count = await _append_attachment_to_state(
        state=state,
        user_id=5,
        draft_attachment=_make_draft_attachment("doc.pdf", "application/pdf", 4096),
    )

    assert photo_count == 1
    assert doc_count == 2
    attachments = _extract_attachments(await state.get_data())
    assert [item.file_type for item in attachments] == ["image/jpeg", "application/pdf"]
