from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.bot.rate_limit import RateLimiter, RateLimiterUnavailableError

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, rate_limiter: RateLimiter) -> None:
        self._rate_limiter = rate_limiter
        self._degraded_mode_logged = False

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        event_user = data.get("event_from_user")
        user_id = getattr(event_user, "id", None)
        if not isinstance(user_id, int):
            return await handler(event, data)

        try:
            decision = await self._rate_limiter.check_user(user_id=user_id)
        except RateLimiterUnavailableError as exc:
            if not self._degraded_mode_logged:
                logger.warning("Rate limiter is temporarily unavailable: %s", exc)
                self._degraded_mode_logged = True
            return await handler(event, data)

        if self._degraded_mode_logged:
            logger.info("Rate limiter recovered.")
            self._degraded_mode_logged = False

        if decision.allowed:
            return await handler(event, data)

        await self._notify_user(event=event, retry_after_seconds=decision.retry_after_seconds)
        return None

    async def _notify_user(self, *, event: TelegramObject, retry_after_seconds: int) -> None:
        retry_after_seconds = max(1, retry_after_seconds)
        message_text = (
            "Слишком много действий за короткое время. "
            f"Попробуйте снова через {retry_after_seconds} сек."
        )

        if isinstance(event, Message):
            await event.answer(message_text)
            return

        if isinstance(event, CallbackQuery):
            await event.answer(message_text, show_alert=True)
