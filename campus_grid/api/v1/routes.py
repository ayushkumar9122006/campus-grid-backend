from fastapi import APIRouter

from campus_grid.api.v1.endpoints.audit_log import router as audit_log_router
from campus_grid.api.v1.endpoints.auth import router as auth_router
from campus_grid.api.v1.endpoints.booking import router as booking_router
from campus_grid.api.v1.endpoints.resource import router as resource_router
from campus_grid.api.v1.endpoints.user import router as user_router

routers = APIRouter()

routers.include_router(auth_router)
routers.include_router(user_router)
routers.include_router(resource_router)
routers.include_router(booking_router)
routers.include_router(audit_log_router)
