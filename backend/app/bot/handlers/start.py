import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.exc import SQLAlchemyError

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.states import AuthStates
from app.bot.texts import WELCOME_AUTHORIZED_TEXT, WELCOME_UNAUTHORIZED_TEXT
from app.db.session import AsyncSessionFactory
from app.services.invite_service import authorize_user_with_invite_code
from app.services.upload_service import cleanup_draft_attachments, load_draft_attachments
from app.services.user_service import ensure_telegram_user

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    # Safety cleanup in case user restarts flow while draft attachments already exist in FSM.
    data = await state.get_data()
    raw_attachments = data.get("attachments", [])
    if isinstance(raw_attachments, list) and raw_attachments:
        try:
            cleanup_draft_attachments(load_draft_attachments(raw_attachments))
        except Exception:
            logger.exception("Failed to cleanup draft attachments on /start reset.")

    try:
        async with AsyncSessionFactory() as session:
            user = await ensure_telegram_user(session, message.from_user)
            await session.commit()

            if user.is_authorized:
                await state.clear()
                await message.answer(
                    WELCOME_AUTHORIZED_TEXT,
                    reply_markup=main_menu_keyboard(),
                )
                return
    except SQLAlchemyError as exc:
        logger.exception("Database error in /start handler: %s", exc)
        await message.answer("Временная ошибка сервиса. Попробуйте чуть позже.")
        return

    await state.set_state(AuthStates.waiting_invite_code)
    await message.answer(WELCOME_UNAUTHORIZED_TEXT)


@router.message(AuthStates.waiting_invite_code, F.text)
async def invite_code_input(message: Message, state: FSMContext) -> None:
    if message.from_user is None or message.text is None:
        await message.answer("Не удалось прочитать код. Попробуйте снова.")
        return

    try:
        async with AsyncSessionFactory() as session:
            user = await ensure_telegram_user(session, message.from_user)
            await session.commit()
            result = await authorize_user_with_invite_code(session, user, message.text)
    except SQLAlchemyError as exc:
        logger.exception("Database error in invite-code handler: %s", exc)
        await message.answer("Временная ошибка сервиса. Попробуйте чуть позже.")
        return

    if result.success:
        await state.clear()
        await message.answer(result.message)
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard())
        return

    await message.answer(result.message)


@router.message(AuthStates.waiting_invite_code)
async def invite_code_non_text(message: Message) -> None:
    await message.answer("Введите invite code текстом.")
