from __future__ import annotations

import asyncio
import logging
import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable, Protocol

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class RateLimiterUnavailableError(RuntimeError):
    pass


class RateLimiter(Protocol):
    async def check_user(self, user_id: int) -> RateLimitDecision:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


class DisabledRateLimiter:
    async def check_user(self, user_id: int) -> RateLimitDecision:
        return RateLimitDecision(allowed=True)

    async def close(self) -> None:
        return None


class InMemoryRateLimiter:
    def __init__(
        self,
        *,
        max_events: int,
        window_seconds: int,
        block_seconds: int,
        time_provider: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_events = max_events
        self._window_seconds = window_seconds
        self._block_seconds = block_seconds
        self._time_provider = time_provider
        self._events: dict[int, deque[float]] = defaultdict(deque)
        self._blocked_until: dict[int, float] = {}
        self._lock = asyncio.Lock()

    async def check_user(self, user_id: int) -> RateLimitDecision:
        now = self._time_provider()
        async with self._lock:
            blocked_until = self._blocked_until.get(user_id)
            if blocked_until is not None and blocked_until > now:
                retry_after = max(1, math.ceil(blocked_until - now))
                return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)

            if blocked_until is not None and blocked_until <= now:
                self._blocked_until.pop(user_id, None)

            user_events = self._events[user_id]
            while user_events and now - user_events[0] >= self._window_seconds:
                user_events.popleft()

            if len(user_events) >= self._max_events:
                new_blocked_until = now + self._block_seconds
                self._blocked_until[user_id] = new_blocked_until
                user_events.clear()
                return RateLimitDecision(allowed=False, retry_after_seconds=self._block_seconds)

            user_events.append(now)
            return RateLimitDecision(allowed=True)

    async def close(self) -> None:
        async with self._lock:
            self._events.clear()
            self._blocked_until.clear()


class RedisRateLimiter:
    def __init__(
        self,
        *,
        redis_client: Any,
        max_events: int,
        window_seconds: int,
        block_seconds: int,
        key_prefix: str = "aerotrust:bot:rate_limit",
    ) -> None:
        self._redis = redis_client
        self._max_events = max_events
        self._window_seconds = window_seconds
        self._block_seconds = block_seconds
        self._key_prefix = key_prefix

    def _counter_key(self, user_id: int) -> str:
        return f"{self._key_prefix}:counter:{user_id}"

    def _block_key(self, user_id: int) -> str:
        return f"{self._key_prefix}:block:{user_id}"

    async def check_user(self, user_id: int) -> RateLimitDecision:
        counter_key = self._counter_key(user_id)
        block_key = self._block_key(user_id)
        try:
            block_ttl = await self._redis.ttl(block_key)
            if block_ttl is not None and block_ttl > 0:
                return RateLimitDecision(allowed=False, retry_after_seconds=int(block_ttl))

            current_count = await self._redis.incr(counter_key)
            if current_count == 1:
                await self._redis.expire(counter_key, self._window_seconds)

            if current_count > self._max_events:
                await self._redis.set(block_key, "1", ex=self._block_seconds)
                await self._redis.delete(counter_key)
                retry_after = await self._redis.ttl(block_key)
                if retry_after is None or retry_after <= 0:
                    retry_after = self._block_seconds
                return RateLimitDecision(
                    allowed=False,
                    retry_after_seconds=int(retry_after),
                )

            return RateLimitDecision(allowed=True)
        except Exception as exc:
            raise RateLimiterUnavailableError("Redis rate limiter is unavailable.") from exc

    async def close(self) -> None:
        close_method = getattr(self._redis, "aclose", None)
        if callable(close_method):
            await close_method()
            return
        await self._redis.close()


async def build_rate_limiter() -> RateLimiter:
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.bot_rate_limit_enabled:
        logger.info("Bot rate limiting is disabled by config.")
        return DisabledRateLimiter()

    if (
        settings.bot_rate_limit_max_events <= 0
        or settings.bot_rate_limit_window_seconds <= 0
        or settings.bot_rate_limit_block_seconds <= 0
    ):
        logger.warning(
            "Invalid rate limit config detected; rate limiting is disabled. "
            "BOT_RATE_LIMIT_MAX_EVENTS=%s BOT_RATE_LIMIT_WINDOW_SECONDS=%s BOT_RATE_LIMIT_BLOCK_SECONDS=%s",
            settings.bot_rate_limit_max_events,
            settings.bot_rate_limit_window_seconds,
            settings.bot_rate_limit_block_seconds,
        )
        return DisabledRateLimiter()

    if settings.redis_url:
        try:
            import redis.asyncio as redis

            redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            await redis_client.ping()
            logger.info("Bot rate limiter is backed by Redis.")
            return RedisRateLimiter(
                redis_client=redis_client,
                max_events=settings.bot_rate_limit_max_events,
                window_seconds=settings.bot_rate_limit_window_seconds,
                block_seconds=settings.bot_rate_limit_block_seconds,
            )
        except Exception as exc:
            logger.warning(
                "Redis is unavailable for bot rate limiting, fallback to in-memory limiter: %s",
                exc,
            )

    logger.info("Bot rate limiter is backed by in-memory storage.")
    return InMemoryRateLimiter(
        max_events=settings.bot_rate_limit_max_events,
        window_seconds=settings.bot_rate_limit_window_seconds,
        block_seconds=settings.bot_rate_limit_block_seconds,
    )
