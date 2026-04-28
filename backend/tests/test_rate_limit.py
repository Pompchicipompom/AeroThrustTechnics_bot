import asyncio

from app.bot.rate_limit import DisabledRateLimiter, InMemoryRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def tick(self, seconds: float) -> None:
        self.now += seconds

    def __call__(self) -> float:
        return self.now


def test_in_memory_rate_limiter_blocks_after_threshold() -> None:
    clock = FakeClock()
    limiter = InMemoryRateLimiter(
        max_events=2,
        window_seconds=10,
        block_seconds=5,
        time_provider=clock,
    )

    assert asyncio.run(limiter.check_user(user_id=1001)).allowed
    assert asyncio.run(limiter.check_user(user_id=1001)).allowed

    blocked = asyncio.run(limiter.check_user(user_id=1001))
    assert not blocked.allowed
    assert blocked.retry_after_seconds == 5


def test_in_memory_rate_limiter_unblocks_after_block_window() -> None:
    clock = FakeClock()
    limiter = InMemoryRateLimiter(
        max_events=1,
        window_seconds=10,
        block_seconds=3,
        time_provider=clock,
    )

    assert asyncio.run(limiter.check_user(user_id=2002)).allowed
    blocked = asyncio.run(limiter.check_user(user_id=2002))
    assert not blocked.allowed
    assert blocked.retry_after_seconds == 3

    clock.tick(3.1)
    allowed_again = asyncio.run(limiter.check_user(user_id=2002))
    assert allowed_again.allowed


def test_disabled_rate_limiter_allows_everything() -> None:
    limiter = DisabledRateLimiter()
    for _ in range(5):
        assert asyncio.run(limiter.check_user(user_id=3003)).allowed
