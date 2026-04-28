import logging
from asyncio import Lock
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import SQLAlchemyError

from app.bot.constants import (
    ACTION_CANCEL,
    ACTION_GO_TO_CONFIRMATION,
    ACTION_SKIP_ATTACHMENTS,
    CALLBACK_CANCEL_REPORT,
    CALLBACK_CATEGORY_PREFIX,
    CALLBACK_CONFIRM_REPORT,
    CALLBACK_MODE_PREFIX,
    MENU_SEND_REPORT,
    SUBMIT_MODE_BY_VALUE,
)
from app.bot.handlers.auth_guard import (
    ensure_authorized_callback_user,
    ensure_authorized_message_user,
)
from app.bot.handlers.menu import show_main_menu
from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.keyboards.report import (
    report_attachments_keyboard,
    report_category_keyboard,
    report_confirmation_keyboard,
    report_mode_keyboard,
    report_text_keyboard,
)
from app.bot.states import ReportStates
from app.bot.texts import (
    REPORT_ACCEPTED_TEXT_TEMPLATE,
    REPORT_ATTACHMENTS_PROMPT,
    REPORT_CATEGORY_TEXT,
    REPORT_INTRO_TEXT,
    REPORT_TEXT_PROMPT,
)
from app.core.config import get_settings
from app.core.reporting import CATEGORY_LABELS_RU, SUBMIT_MODE_LABELS_RU
from app.db.session import AsyncSessionFactory
from app.models.enums import SubmitMode
from app.services.report_service import ReportDraft, create_report_from_draft
from app.services.upload_service import (
    AttachmentValidationError,
    DraftAttachment,
    cleanup_draft_attachments,
    load_draft_attachments,
    save_telegram_file_to_temp,
    validate_document_payload,
)
from app.services.user_service import ensure_telegram_user

router = Router()
logger = logging.getLogger(__name__)
report_states_filter = StateFilter(*ReportStates.__all_states__)
_ATTACHMENT_STATE_LOCKS: dict[int, Lock] = {}


def _get_attachment_state_lock(user_id: int) -> Lock:
    lock = _ATTACHMENT_STATE_LOCKS.get(user_id)
    if lock is None:
        lock = Lock()
        _ATTACHMENT_STATE_LOCKS[user_id] = lock
    return lock


def _serialize_attachments(attachments: list[DraftAttachment]) -> list[dict[str, str | int]]:
    return [attachment.to_dict() for attachment in attachments]


def _extract_attachments(data: dict[str, object]) -> list[DraftAttachment]:
    raw = data.get("attachments", [])
    if not isinstance(raw, list):
        return []
    return load_draft_attachments(raw_attachments=raw)


async def _append_attachment_to_state(
    *,
    state: FSMContext,
    user_id: int,
    draft_attachment: DraftAttachment,
) -> int:
    lock = _get_attachment_state_lock(user_id)
    async with lock:
        data = await state.get_data()
        attachments = _extract_attachments(data)
        settings = get_settings()
        if len(attachments) >= settings.max_attachments_per_report:
            raise AttachmentValidationError(
                f"Достигнут лимит вложений: {settings.max_attachments_per_report}."
            )

        attachments.append(draft_attachment)
        await state.update_data(attachments=_serialize_attachments(attachments))
        return len(attachments)


async def _cleanup_attachments_from_state(state: FSMContext) -> None:
    data = await state.get_data()
    attachments = _extract_attachments(data)
    if attachments:
        cleanup_draft_attachments(attachments)


def _build_summary_text(
    *,
    submit_mode: SubmitMode,
    category: str,
    text: str,
    attachments_count: int,
) -> str:
    mode_label = SUBMIT_MODE_LABELS_RU[submit_mode]
    category_label = CATEGORY_LABELS_RU.get(category, category)
    return (
        "Проверьте сообщение перед отправкой:\n\n"
        f"<b>Режим:</b> {mode_label}\n"
        f"<b>Категория:</b> {category_label}\n"
        f"<b>Текст:</b>\n{escape(text)}\n\n"
        f"<b>Вложений:</b> {attachments_count}"
    )


async def _send_confirmation_step(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    submit_mode_value = str(data.get("submit_mode", ""))
    category = str(data.get("category", ""))
    report_text = str(data.get("text", "")).strip()
    submit_mode = SUBMIT_MODE_BY_VALUE.get(submit_mode_value)
    if submit_mode is None or not category or not report_text:
        await message.answer("Не удалось собрать данные сообщения. Начните заново.")
        await _cleanup_attachments_from_state(state)
        await state.clear()
        await show_main_menu(message)
        return

    attachments = _extract_attachments(data)
    await state.set_state(ReportStates.waiting_confirmation)
    await message.answer(
        _build_summary_text(
            submit_mode=submit_mode,
            category=category,
            text=report_text,
            attachments_count=len(attachments),
        ),
        reply_markup=report_confirmation_keyboard(),
    )


async def _cancel_report_creation(message: Message, state: FSMContext) -> None:
    await _cleanup_attachments_from_state(state)
    await state.clear()
    await message.answer("Создание сообщения отменено.", reply_markup=main_menu_keyboard())


@router.message(F.text == MENU_SEND_REPORT)
async def start_report_flow(message: Message, state: FSMContext) -> None:
    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return

    await _cleanup_attachments_from_state(state)
    await state.clear()
    await state.set_state(ReportStates.choosing_mode)
    await state.update_data(attachments=[])
    await message.answer(REPORT_INTRO_TEXT, reply_markup=report_mode_keyboard())


@router.message(report_states_filter, Command("cancel"))
@router.message(report_states_filter, F.text == ACTION_CANCEL)
async def cancel_report_flow(message: Message, state: FSMContext) -> None:
    await _cancel_report_creation(message, state)


@router.callback_query(report_states_filter, F.data == CALLBACK_CANCEL_REPORT)
async def cancel_report_flow_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is not None:
        await _cancel_report_creation(callback.message, state)
    await callback.answer("Создание сообщения отменено.")


@router.callback_query(ReportStates.choosing_mode, F.data.startswith(CALLBACK_MODE_PREFIX))
async def choose_submit_mode(callback: CallbackQuery, state: FSMContext) -> None:
    user = await ensure_authorized_callback_user(callback, state)
    if user is None:
        return

    mode_value = callback.data.removeprefix(CALLBACK_MODE_PREFIX)
    submit_mode = SUBMIT_MODE_BY_VALUE.get(mode_value)
    if submit_mode is None:
        await callback.answer("Некорректный режим.", show_alert=True)
        return

    await state.update_data(submit_mode=submit_mode.value)
    await state.set_state(ReportStates.choosing_category)
    if callback.message is not None:
        await callback.message.answer(REPORT_CATEGORY_TEXT, reply_markup=report_category_keyboard())
    await callback.answer()


@router.callback_query(ReportStates.choosing_category, F.data.startswith(CALLBACK_CATEGORY_PREFIX))
async def choose_category(callback: CallbackQuery, state: FSMContext) -> None:
    user = await ensure_authorized_callback_user(callback, state)
    if user is None:
        return

    category = callback.data.removeprefix(CALLBACK_CATEGORY_PREFIX)
    if category not in CATEGORY_LABELS_RU:
        await callback.answer("Некорректная категория.", show_alert=True)
        return

    await state.update_data(category=category)
    await state.set_state(ReportStates.waiting_text)
    if callback.message is not None:
        await callback.message.answer(REPORT_TEXT_PROMPT, reply_markup=report_text_keyboard())
    await callback.answer()


@router.message(ReportStates.waiting_text, F.text)
async def capture_text(message: Message, state: FSMContext) -> None:
    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("Текст не может быть пустым. Введите сообщение.")
        return

    await state.update_data(text=text)
    await state.set_state(ReportStates.waiting_attachments)
    await message.answer(REPORT_ATTACHMENTS_PROMPT, reply_markup=report_attachments_keyboard())


@router.message(ReportStates.waiting_text)
async def capture_text_non_text(message: Message) -> None:
    await message.answer("На этом шаге нужен текст сообщения.")


@router.message(ReportStates.waiting_attachments, F.text.in_([ACTION_SKIP_ATTACHMENTS, ACTION_GO_TO_CONFIRMATION]))
async def complete_attachments_step(message: Message, state: FSMContext) -> None:
    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return
    await _send_confirmation_step(message, state)


@router.message(ReportStates.waiting_attachments, F.photo)
async def upload_photo(message: Message, state: FSMContext) -> None:
    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return

    if message.photo is None:
        await message.answer("Не удалось прочитать фото. Попробуйте снова.")
        return

    photo = message.photo[-1]
    try:
        draft_attachment = await save_telegram_file_to_temp(
            bot=message.bot,
            file_id=photo.file_id,
            suggested_file_name=f"photo_{photo.file_unique_id}.jpg",
            file_type="image/jpeg",
            file_size=photo.file_size,
        )
    except AttachmentValidationError as exc:
        await message.answer(str(exc))
        return
    except Exception as exc:
        logger.exception("Failed to save photo attachment: %s", exc)
        await message.answer("Не удалось сохранить фото. Попробуйте еще раз.")
        return

    try:
        attachments_count = await _append_attachment_to_state(
            state=state,
            user_id=user.id,
            draft_attachment=draft_attachment,
        )
    except AttachmentValidationError as exc:
        cleanup_draft_attachments([draft_attachment])
        await message.answer(str(exc))
        return

    await message.answer(
        f"Фото добавлено. Вложений: {attachments_count}.",
        reply_markup=report_attachments_keyboard(),
    )


@router.message(ReportStates.waiting_attachments, F.document)
async def upload_document(message: Message, state: FSMContext) -> None:
    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return

    document = message.document
    if document is None:
        await message.answer("Не удалось прочитать файл. Попробуйте снова.")
        return

    file_name = document.file_name or f"document_{document.file_unique_id}"
    try:
        validate_document_payload(
            file_name=file_name,
            mime_type=document.mime_type,
            file_size=document.file_size,
        )
        draft_attachment = await save_telegram_file_to_temp(
            bot=message.bot,
            file_id=document.file_id,
            suggested_file_name=file_name,
            file_type=document.mime_type or "application/octet-stream",
            file_size=document.file_size,
        )
    except AttachmentValidationError as exc:
        await message.answer(str(exc))
        return
    except Exception as exc:
        logger.exception("Failed to save document attachment: %s", exc)
        await message.answer("Не удалось сохранить файл. Попробуйте еще раз.")
        return

    try:
        attachments_count = await _append_attachment_to_state(
            state=state,
            user_id=user.id,
            draft_attachment=draft_attachment,
        )
    except AttachmentValidationError as exc:
        cleanup_draft_attachments([draft_attachment])
        await message.answer(str(exc))
        return

    await message.answer(
        f"Файл добавлен. Вложений: {attachments_count}.",
        reply_markup=report_attachments_keyboard(),
    )


@router.message(ReportStates.waiting_attachments)
async def waiting_attachments_invalid_input(message: Message) -> None:
    await message.answer(
        "Пришлите фото/документ или нажмите «К подтверждению»/«Пропустить».",
        reply_markup=report_attachments_keyboard(),
    )


@router.callback_query(ReportStates.waiting_confirmation, F.data == CALLBACK_CONFIRM_REPORT)
async def confirm_report(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer("Не удалось определить пользователя.", show_alert=True)
        return

    data = await state.get_data()
    submit_mode_value = str(data.get("submit_mode", ""))
    category = str(data.get("category", ""))
    report_text = str(data.get("text", ""))
    submit_mode = SUBMIT_MODE_BY_VALUE.get(submit_mode_value)

    if submit_mode is None or not category or not report_text:
        await callback.answer("Данные сообщения повреждены. Начните заново.", show_alert=True)
        if callback.message is not None:
            await _cancel_report_creation(callback.message, state)
        return

    attachments = _extract_attachments(data)
    try:
        async with AsyncSessionFactory() as session:
            user = await ensure_telegram_user(session, callback.from_user)
            if not user.is_authorized:
                await state.clear()
                await callback.answer("Нужна авторизация.", show_alert=True)
                if callback.message is not None:
                    await callback.message.answer("Для доступа введите invite code.")
                return

            report = await create_report_from_draft(
                session,
                author=user,
                draft=ReportDraft(
                    submit_mode=submit_mode,
                    category=category,
                    text=report_text,
                    attachments=attachments,
                ),
            )
    except (ValueError, AttachmentValidationError) as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    except SQLAlchemyError as exc:
        logger.exception("Database error on report creation: %s", exc)
        await callback.answer("Ошибка БД. Попробуйте позже.", show_alert=True)
        return
    except Exception as exc:
        logger.exception("Unexpected error on report creation: %s", exc)
        await callback.answer("Не удалось отправить сообщение.", show_alert=True)
        return

    await state.clear()
    if callback.message is not None:
        await callback.message.answer(
            REPORT_ACCEPTED_TEXT_TEMPLATE.format(public_number=report.public_number),
            reply_markup=main_menu_keyboard(),
        )
    await callback.answer("Отправлено.")


@router.message(ReportStates.waiting_confirmation)
async def waiting_confirmation_invalid_input(message: Message) -> None:
    await message.answer("Используйте кнопку «Подтвердить» или «Отменить».")


@router.message(ReportStates.choosing_mode)
@router.message(ReportStates.choosing_category)
async def inline_choice_invalid_input(message: Message) -> None:
    await message.answer("Выберите вариант с помощью кнопок в сообщении выше.")
