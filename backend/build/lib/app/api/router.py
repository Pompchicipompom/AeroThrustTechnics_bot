from fastapi import APIRouter

from app.api.routes.admin_analytics import router as admin_analytics_router
from app.api.routes.admin_audit import router as admin_audit_router
from app.api.routes.admin_auth import router as admin_auth_router
from app.api.routes.admin_reports import router as admin_reports_router
from app.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(admin_auth_router)
api_router.include_router(admin_reports_router)
api_router.include_router(admin_analytics_router)
api_router.include_router(admin_audit_router)
