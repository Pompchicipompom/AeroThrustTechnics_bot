from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.models.enums import AdminRole


def _active_only(statement: Select[tuple[AdminUser]]) -> Select[tuple[AdminUser]]:
    return statement.where(AdminUser.is_active.is_(True))


async def get_active_by_email(session: AsyncSession, email: str) -> AdminUser | None:
    statement = _active_only(select(AdminUser)).where(AdminUser.email == email).limit(1)
    return await session.scalar(statement)


async def get_active_by_id(session: AsyncSession, admin_user_id: int) -> AdminUser | None:
    statement = _active_only(select(AdminUser)).where(AdminUser.id == admin_user_id).limit(1)
    return await session.scalar(statement)


async def get_by_email(session: AsyncSession, email: str) -> AdminUser | None:
    statement = select(AdminUser).where(AdminUser.email == email).limit(1)
    return await session.scalar(statement)


async def create_admin_user(
    session: AsyncSession,
    *,
    email: str,
    password_hash: str,
    role: AdminRole,
    zone: str | None,
) -> AdminUser:
    admin_user = AdminUser(
        email=email,
        password_hash=password_hash,
        role=role,
        zone=zone,
        is_active=True,
    )
    session.add(admin_user)
    await session.flush()
    return admin_user
