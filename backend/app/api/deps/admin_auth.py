from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.admin_user import AdminUser
from app.models.enums import AdminRole
from app.core.security import decode_admin_access_token
from app.repositories.admin_users import get_active_by_id

http_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired admin token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> AdminUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    token = credentials.credentials.strip()
    if not token:
        raise _unauthorized()

    try:
        payload = decode_admin_access_token(token)
    except ValueError as exc:
        raise _unauthorized() from exc

    admin_user = await get_active_by_id(session, payload.admin_user_id)
    if admin_user is None:
        raise _unauthorized()

    return admin_user


def require_roles(*roles: AdminRole) -> Callable[[AdminUser], AdminUser]:
    allowed = {role.value for role in roles}

    async def _checker(current_admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
        if current_admin.role.value not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions.",
            )
        return current_admin

    return _checker
