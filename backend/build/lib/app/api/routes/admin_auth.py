from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.admin_auth import get_current_admin
from app.db.session import get_db_session
from app.models.admin_user import AdminUser
from app.schemas.admin_auth import (
    AdminLoginRequest,
    AdminProfileResponse,
    AdminTokenResponse,
)
from app.services.admin_auth_service import authenticate_admin
from app.services.audit_service import log_admin_action

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(
    payload: AdminLoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AdminTokenResponse:
    login_result = await authenticate_admin(
        session,
        email=payload.email,
        password=payload.password,
    )
    if login_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    try:
        await log_admin_action(
            session,
            admin_user_id=login_result.admin_user.id,
            entity_type="admin_user",
            entity_id=login_result.admin_user.id,
            action="login",
            payload_json={"role": login_result.admin_user.role.value},
        )
        await session.commit()
    except Exception:
        await session.rollback()

    return AdminTokenResponse(
        access_token=login_result.token,
        expires_at=login_result.expires_at,
    )


@router.get("/me", response_model=AdminProfileResponse)
async def admin_me(current_admin: AdminUser = Depends(get_current_admin)) -> AdminProfileResponse:
    return AdminProfileResponse(
        id=current_admin.id,
        email=current_admin.email,
        role=current_admin.role.value,
        zone=current_admin.zone,
    )
