from datetime import datetime
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import SQLAlchemyError

from app.bot.constants import (
    CALLBACK_USER_REPORTS_LIST,
    CALLBACK_USER_REPORTS_MENU,
    CALLBACK_USER_REPORT_DETAIL_PREFIX,
    MENU_REPORT_STATUSES,
)
from app.bot.handlers.auth_guard import ensure_authorized_callback_user, ensure_authorized_message_user
from app.bot.handlers.menu import show_main_menu
from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.keyboards.report_status import user_report_detail_keyboard, user_reports_list_keyboard
from app.core.reporting import CATEGORY_LABELS_RU, REPORT_STATUS_LABELS_RU, SUBMIT_MODE_LABELS_RU
from app.db.session import AsyncSessionFactory
from app.models.report import Report
from app.services.user_reports_service import get_user_report_detail, list_user_reports

router = Router()
MAX_REPORTS_PER_PAGE = 20


def _format_datetime(value: datetime) -> str:
    current_value = value.astimezone() if value.tzinfo else value
    return current_value.strftime("%d.%m.%Y %H:%M")


def _format_file_size(file_size: int) -> str:
    if file_size < 1024:
        return f"{file_size} Б"
    if file_size < 1024 * 1024:
        return f"{file_size / 1024:.1f} КБ"
    return f"{file_size / (1024 * 1024):.1f} МБ"


def _status_label(report: Report) -> str:
    return REPORT_STATUS_LABELS_RU.get(report.status, report.status.value)


def _build_report_list_text(reports: list[Report]) -> str:
    lines = ["<b>Ваши обращения:</b>", ""]
    for report in reports:
        lines.append(f"• № {escape(report.public_number)} — {_status_label(report)}")
    lines.append("")
    lines.append("Нажмите на обращение, чтобы открыть подробности.")
    return "\n".join(lines)


def _build_report_list_buttons(reports: list[Report]) -> list[tuple[int, str]]:
    return [
        (
            report.id,
            f"№{report.public_number} • {_status_label(report)}",
        )
        for report in reports
    ]


def _build_attachments_block(report: Report) -> str:
    attachments = sorted(report.attachments, key=lambda item: item.id)
    if not attachments:
        return "<b>Вложения:</b> нет"

    lines = [f"<b>Вложения:</b> {len(attachments)}"]
    for attachment in attachments:
        lines.append(f"• {escape(attachment.file_name)} ({_format_file_size(attachment.file_size)})")
    return "\n".join(lines)


def _build_report_detail_text(report: Report) -> str:
    category_label = CATEGORY_LABELS_RU.get(report.category, report.category)
    mode_label = SUBMIT_MODE_LABELS_RU.get(report.submit_mode, report.submit_mode.value)
    return (
        f"<b>Номер обращения:</b> {escape(report.public_number)}\n"
        f"<b>Статус:</b> {_status_label(report)}\n"
        f"<b>Категория:</b> {escape(category_label)}\n"
        f"<b>Тип:</b> {escape(mode_label)}\n"
        f"<b>Дата:</b> {_format_datetime(report.created_at)}\n\n"
        f"<b>Текст обращения:</b>\n{escape(report.text)}\n\n"
        f"{_build_attachments_block(report)}"
    )


async def _send_user_reports_list(
    message: Message,
    *,
    user_id: int,
) -> None:
    try:
        async with AsyncSessionFactory() as session:
            reports = await list_user_reports(
                session,
                user_id=user_id,
                limit=MAX_REPORTS_PER_PAGE,
            )
    except SQLAlchemyError:
        await message.answer("Не удалось загрузить обращения. Попробуйте позже.")
        return

    if not reports:
        await message.answer(
            "У вас пока нет обращений.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        _build_report_list_text(reports),
        reply_markup=user_reports_list_keyboard(_build_report_list_buttons(reports)),
    )


@router.message(F.text == MENU_REPORT_STATUSES)
async def my_reports_entrypoint(message: Message, state: FSMContext) -> None:
    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return
    await _send_user_reports_list(message, user_id=user.id)


@router.callback_query(F.data == CALLBACK_USER_REPORTS_LIST)
async def my_reports_list_callback(callback: CallbackQuery, state: FSMContext) -> None:
    user = await ensure_authorized_callback_user(callback, state)
    if user is None:
        return

    if callback.message is not None:
        await _send_user_reports_list(callback.message, user_id=user.id)
    await callback.answer()


@router.callback_query(F.data.startswith(CALLBACK_USER_REPORT_DETAIL_PREFIX))
async def my_report_detail_callback(callback: CallbackQuery, state: FSMContext) -> None:
    user = await ensure_authorized_callback_user(callback, state)
    if user is None:
        return

    callback_data = callback.data or ""
    report_id_raw = callback_data.removeprefix(CALLBACK_USER_REPORT_DETAIL_PREFIX).strip()
    if not report_id_raw.isdigit():
        await callback.answer("Обращение не найдено или недоступно", show_alert=True)
        return

    report_id = int(report_id_raw)
    try:
        async with AsyncSessionFactory() as session:
            report = await get_user_report_detail(
                session,
                user_id=user.id,
                report_id=report_id,
            )
    except SQLAlchemyError:
        await callback.answer("Ошибка загрузки обращения.", show_alert=True)
        return

    if report is None:
        if callback.message is not None:
            await callback.message.answer("Обращение не найдено или недоступно")
        await callback.answer("Обращение не найдено или недоступно", show_alert=True)
        return

    if callback.message is not None:
        await callback.message.answer(
            _build_report_detail_text(report),
            reply_markup=user_report_detail_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == CALLBACK_USER_REPORTS_MENU)
async def my_reports_back_to_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    user = await ensure_authorized_callback_user(callback, state)
    if user is None:
        return

    if callback.message is not None:
        await show_main_menu(callback.message)
    await callback.answer()
