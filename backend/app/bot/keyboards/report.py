from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.bot.constants import (
    ACTION_CANCEL,
    ACTION_GO_TO_CONFIRMATION,
    ACTION_SKIP_ATTACHMENTS,
    CALLBACK_CANCEL_REPORT,
    CALLBACK_CATEGORY_PREFIX,
    CALLBACK_CONFIRM_REPORT,
    CALLBACK_MODE_PREFIX,
)
from app.core.reporting import CATEGORY_LABELS_RU
from app.models.enums import SubmitMode


def report_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыто",
                    callback_data=f"{CALLBACK_MODE_PREFIX}{SubmitMode.OPEN.value}",
                ),
                InlineKeyboardButton(
                    text="Анонимно",
                    callback_data=f"{CALLBACK_MODE_PREFIX}{SubmitMode.ANONYMOUS.value}",
                ),
            ],
            [InlineKeyboardButton(text=ACTION_CANCEL, callback_data=CALLBACK_CANCEL_REPORT)],
        ]
    )


def report_category_keyboard() -> InlineKeyboardMarkup:
    category_rows = [
        ["safety", "quality"],
        ["process", "improvements"],
        ["ethics", "general"],
    ]

    rows: list[list[InlineKeyboardButton]] = []
    for category_row in category_rows:
        row_buttons: list[InlineKeyboardButton] = []
        for category_code in category_row:
            label = CATEGORY_LABELS_RU.get(category_code, category_code)
            row_buttons.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"{CALLBACK_CATEGORY_PREFIX}{category_code}",
                )
            )
        rows.append(row_buttons)

    rows.append([InlineKeyboardButton(text=ACTION_CANCEL, callback_data=CALLBACK_CANCEL_REPORT)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def report_text_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=ACTION_CANCEL)]],
        resize_keyboard=True,
        input_field_placeholder="Введите текст сообщения",
    )


def report_attachments_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ACTION_GO_TO_CONFIRMATION), KeyboardButton(text=ACTION_SKIP_ATTACHMENTS)],
            [KeyboardButton(text=ACTION_CANCEL)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Пришлите фото или документ",
    )


def report_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Подтвердить", callback_data=CALLBACK_CONFIRM_REPORT),
                InlineKeyboardButton(text=ACTION_CANCEL, callback_data=CALLBACK_CANCEL_REPORT),
            ]
        ]
    )
