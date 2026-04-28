from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.constants import (
    CALLBACK_USER_REPORTS_LIST,
    CALLBACK_USER_REPORTS_MENU,
    CALLBACK_USER_REPORT_DETAIL_PREFIX,
)


def user_reports_list_keyboard(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f"{CALLBACK_USER_REPORT_DETAIL_PREFIX}{report_id}",
            )
        ]
        for report_id, label in items
    ]
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=CALLBACK_USER_REPORTS_MENU)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_report_detail_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад к списку", callback_data=CALLBACK_USER_REPORTS_LIST)],
            [InlineKeyboardButton(text="В главное меню", callback_data=CALLBACK_USER_REPORTS_MENU)],
        ]
    )

