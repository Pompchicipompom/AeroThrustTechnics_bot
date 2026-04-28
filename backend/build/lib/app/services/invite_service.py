from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.invite_codes import get_available_by_code


@dataclass(slots=True)
class InviteAuthorizationResult:
    success: bool
    message: str


async def authorize_user_with_invite_code(
    session: AsyncSession,
    user: User,
    raw_code: str,
) -> InviteAuthorizationResult:
    code = raw_code.strip()
    if not code:
        return InviteAuthorizationResult(success=False, message="Invite code не может быть пустым.")

    if user.is_authorized:
        return InviteAuthorizationResult(
            success=True,
            message="Вы уже авторизованы. Можно переходить к работе с ботом.",
        )

    invite_code = await get_available_by_code(session, code)
    if invite_code is None:
        return InviteAuthorizationResult(
            success=False,
            message="Invite code не найден или больше не активен. Попробуйте еще раз.",
        )

    invite_code.used_count += 1
    user.is_authorized = True
    user.invite_code_id = invite_code.id

    if invite_code.max_uses is not None and invite_code.used_count >= invite_code.max_uses:
        invite_code.is_active = False

    await session.commit()
    return InviteAuthorizationResult(
        success=True,
        message="Код подтвержден. Вы успешно авторизованы.",
    )
