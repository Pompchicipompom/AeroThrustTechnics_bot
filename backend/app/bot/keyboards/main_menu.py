from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.bot.constants import MENU_HOW_IT_WORKS, MENU_REPORT_STATUSES, MENU_SEND_REPORT


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MENU_SEND_REPORT)],
            [KeyboardButton(text=MENU_HOW_IT_WORKS)],
            [KeyboardButton(text=MENU_REPORT_STATUSES)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


def send_report_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MENU_SEND_REPORT)],
            [KeyboardButton(text=MENU_HOW_IT_WORKS)],
            [KeyboardButton(text=MENU_REPORT_STATUSES)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
