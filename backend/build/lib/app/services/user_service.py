from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.users import create_from_telegram_user, get_by_telegram_id


async def ensure_telegram_user(session: AsyncSession, telegram_user: TelegramUser) -> User:
    user = await get_by_telegram_id(session, telegram_user.id)
    if user is None:
        return await create_from_telegram_user(session, telegram_user)

    profile_changed = False
    if user.telegram_username != telegram_user.username:
        user.telegram_username = telegram_user.username
        profile_changed = True
    if user.telegram_first_name != telegram_user.first_name:
        user.telegram_first_name = telegram_user.first_name
        profile_changed = True
    if user.telegram_last_name != telegram_user.last_name:
        user.telegram_last_name = telegram_user.last_name
        profile_changed = True

    if profile_changed:
        await session.flush()
    return user
