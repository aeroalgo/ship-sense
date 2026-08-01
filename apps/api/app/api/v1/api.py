from fastapi import APIRouter

from app.api.v1.endpoints.admin_audit import router as admin_audit_router
from app.api.v1.endpoints.admin_ota import router as admin_ota_router
from app.api.v1.endpoints.admin_storage import router as admin_storage_router
from app.api.v1.endpoints.assets import router as assets_router
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.series import router as series_router
from app.api.v1.endpoints.setpoints import router as setpoints_router
from app.api.v1.endpoints.session import router as session_router
from app.api.v1.endpoints.stream import router as stream_router
from app.api.v1.endpoints.warnings import router as warnings_router
from app.api.v1.endpoints.watch_schedule import router as watch_schedule_router
from app.api.v1.endpoints.mnemo import router as mnemo_router
from app.api.v1.endpoints.vessel import router as vessel_router

api_router = APIRouter()
api_router.include_router(admin_audit_router)
api_router.include_router(admin_ota_router)
api_router.include_router(admin_storage_router)
api_router.include_router(health_router)
api_router.include_router(reports_router)
api_router.include_router(assets_router)
api_router.include_router(series_router)
api_router.include_router(events_router)
api_router.include_router(setpoints_router)
api_router.include_router(session_router)
api_router.include_router(stream_router)
api_router.include_router(warnings_router)
api_router.include_router(watch_schedule_router)
api_router.include_router(mnemo_router)
api_router.include_router(vessel_router)
