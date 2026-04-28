from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.bot.constants import MENU_ANON_INFO, MENU_HELP, MENU_HOW_IT_WORKS, MENU_SEND_REPORT


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MENU_SEND_REPORT)],
            [KeyboardButton(text=MENU_HOW_IT_WORKS), KeyboardButton(text=MENU_ANON_INFO)],
            [KeyboardButton(text=MENU_HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


def send_report_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=MENU_SEND_REPORT)]],
        resize_keyboard=True,
        input_field_placeholder="Нажмите «Отправить сообщение»",
    )
