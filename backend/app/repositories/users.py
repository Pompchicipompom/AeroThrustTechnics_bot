from aiogram.types import User as TelegramUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    query = select(User).where(User.telegram_id == telegram_id)
    return await session.scalar(query)


async def create_from_telegram_user(session: AsyncSession, telegram_user: TelegramUser) -> User:
    user = User(
        telegram_id=telegram_user.id,
        telegram_username=telegram_user.username,
        telegram_first_name=telegram_user.first_name,
        telegram_last_name=telegram_user.last_name,
        is_authorized=False,
    )
    session.add(user)
    await session.flush()
    return user
