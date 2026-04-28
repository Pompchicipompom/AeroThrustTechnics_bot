from datetime import datetime, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invite_code import InviteCode


async def get_available_by_code(session: AsyncSession, code: str) -> InviteCode | None:
    now = datetime.now(tz=timezone.utc)
    query = (
        select(InviteCode)
        .where(
            and_(
                InviteCode.code == code,
                InviteCode.is_active.is_(True),
                or_(InviteCode.expires_at.is_(None), InviteCode.expires_at > now),
            )
        )
        .limit(1)
    )
    invite_code = await session.scalar(query)
    if invite_code is None:
        return None

    if invite_code.max_uses is not None and invite_code.used_count >= invite_code.max_uses:
        return None
    return invite_code
