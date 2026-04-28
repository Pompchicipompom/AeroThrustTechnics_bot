from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_admin_access_token, verify_password
from app.models.admin_user import AdminUser
from app.repositories.admin_users import get_active_by_email


@dataclass(slots=True, frozen=True)
class AdminLoginResult:
    token: str
    expires_at: datetime
    admin_user: AdminUser


async def authenticate_admin(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> AdminLoginResult | None:
    normalized_email = email.strip().lower()
    admin_user = await get_active_by_email(session, normalized_email)
    if admin_user is None:
        return None

    if not verify_password(password, admin_user.password_hash):
        return None

    token, expires_at = create_admin_access_token(
        admin_user_id=admin_user.id,
        role=admin_user.role.value,
        zone=admin_user.zone,
    )
    return AdminLoginResult(
        token=token,
        expires_at=expires_at,
        admin_user=admin_user,
    )
