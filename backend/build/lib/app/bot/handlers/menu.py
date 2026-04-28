from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.constants import MENU_ANON_INFO, MENU_HELP, MENU_HOW_IT_WORKS, MENU_SEND_REPORT
from app.bot.handlers.auth_guard import ensure_authorized_message_user
from app.bot.keyboards.main_menu import main_menu_keyboard, send_report_keyboard
from app.bot.texts import ANONYMOUS_INFO_TEXT, HELP_TEXT, HOW_IT_WORKS_TEXT, MAIN_MENU_PROMPT

router = Router()
_KNOWN_MENU_MESSAGES = {
    MENU_SEND_REPORT,
    MENU_HOW_IT_WORKS,
    MENU_ANON_INFO,
    MENU_HELP,
}


async def show_main_menu(message: Message) -> None:
    await message.answer(MAIN_MENU_PROMPT, reply_markup=main_menu_keyboard())


@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext) -> None:
    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return
    await show_main_menu(message)


@router.message(F.text == MENU_HOW_IT_WORKS)
async def how_it_works(message: Message, state: FSMContext) -> None:
    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return
    await message.answer(HOW_IT_WORKS_TEXT, reply_markup=main_menu_keyboard())


@router.message(F.text == MENU_ANON_INFO)
async def anonymous_info(message: Message, state: FSMContext) -> None:
    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return
    await message.answer(ANONYMOUS_INFO_TEXT, reply_markup=main_menu_keyboard())


@router.message(F.text == MENU_HELP)
@router.message(Command("help"))
async def help_info(message: Message, state: FSMContext) -> None:
    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.message(StateFilter(None), F.text)
async def outside_report_flow_message(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text in _KNOWN_MENU_MESSAGES or text.startswith("/"):
        return

    user = await ensure_authorized_message_user(message, state)
    if user is None:
        return

    await message.answer(
        "Сейчас вы не создаёте обращение.\n\n"
        "Нажмите «Отправить сообщение», чтобы начать.",
        reply_markup=send_report_keyboard(),
    )
