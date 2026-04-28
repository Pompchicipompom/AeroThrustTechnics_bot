from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import SQLAlchemyError

from app.bot.states import AuthStates
from app.db.session import AsyncSessionFactory
from app.models.user import User
from app.services.user_service import ensure_telegram_user


async def ensure_authorized_message_user(message: Message, state: FSMContext) -> User | None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя.")
        return None

    try:
        async with AsyncSessionFactory() as session:
            user = await ensure_telegram_user(session, message.from_user)
            await session.commit()
    except SQLAlchemyError:
        await message.answer("Временная ошибка сервиса. Попробуйте позже.")
        return None

    if user.is_authorized:
        return user

    await state.set_state(AuthStates.waiting_invite_code)
    await message.answer("Для доступа введите invite code.")
    return None


async def ensure_authorized_callback_user(
    callback: CallbackQuery,
    state: FSMContext,
) -> User | None:
    if callback.from_user is None:
        await callback.answer("Не удалось определить пользователя.", show_alert=True)
        return None

    try:
        async with AsyncSessionFactory() as session:
            user = await ensure_telegram_user(session, callback.from_user)
            await session.commit()
    except SQLAlchemyError:
        await callback.answer("Ошибка сервиса. Попробуйте позже.", show_alert=True)
        return None

    if user.is_authorized:
        return user

    await state.set_state(AuthStates.waiting_invite_code)
    await callback.answer("Нужна авторизация.", show_alert=True)
    if callback.message is not None:
        await callback.message.answer("Для доступа введите invite code.")
    return None
