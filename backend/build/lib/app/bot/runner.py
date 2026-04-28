import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ErrorEvent

from app.bot.handlers.menu import router as menu_router
from app.bot.middlewares.rate_limit import RateLimitMiddleware
from app.bot.rate_limit import build_rate_limiter
from app.bot.handlers.report_flow import router as report_flow_router
from app.bot.handlers.start import router as start_router
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


async def build_storage() -> RedisStorage | MemoryStorage:
    settings = get_settings()
    if not settings.redis_url:
        return MemoryStorage()

    try:
        storage = RedisStorage.from_url(settings.redis_url)
        await storage.redis.ping()
        return storage
    except Exception as exc:
        logger.warning("Redis is unavailable for FSM, fallback to memory storage: %s", exc)
        return MemoryStorage()


async def on_error(event: ErrorEvent) -> None:
    logger.exception("Unhandled bot error: %s", event.exception)
    if event.update.message is not None:
        try:
            await event.update.message.answer("Внутренняя ошибка. Попробуйте позже.")
        except Exception:
            logger.exception("Failed to send error notification to user.")


async def run_polling() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is empty.")

    configure_logging(settings.log_level)

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    rate_limiter = await build_rate_limiter()
    dp = Dispatcher(storage=await build_storage())
    dp.update.outer_middleware(RateLimitMiddleware(rate_limiter))
    dp.include_router(start_router)
    dp.include_router(report_flow_router)
    dp.include_router(menu_router)
    dp.errors.register(on_error)

    logger.info("Starting Telegram bot polling.")
    try:
        await dp.start_polling(
            bot,
            polling_timeout=settings.bot_polling_timeout,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()
        await dp.storage.close()
        await rate_limiter.close()
        logger.info("Telegram bot stopped.")


def run() -> None:
    asyncio.run(run_polling())


if __name__ == "__main__":
    run()
