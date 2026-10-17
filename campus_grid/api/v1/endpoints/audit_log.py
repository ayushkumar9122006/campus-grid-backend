from typing import Optional
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from campus_grid.core.container import Container
from campus_grid.core.dependencies import require_faculty_or_admin
from campus_grid.model.user import User
from campus_grid.schema.audit_log_schema import AuditLogResponse
from campus_grid.schema.base_schema import PaginatedResponse
from campus_grid.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
@inject
def list_audit_logs(
    user_id: Optional[int] = Query(default=None, description="Filter logs by actor user ID"),
    action: Optional[str] = Query(default=None, description="Filter logs by action"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    service: AuditLogService = Depends(Provide[Container.audit_log_service]),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Inspect immutable system and reservation audit logs (Faculty & Admin only)."""
    return service.list_logs(user_id=user_id, action=action, page=page, page_size=page_size)
