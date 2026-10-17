import math
from typing import Any, Dict, Optional

from campus_grid.model.audit_log import AuditLog
from campus_grid.repository.audit_log_repository import AuditLogRepository
from campus_grid.services.base_service import BaseService


class AuditLogService(BaseService[AuditLog]):
    def __init__(self, audit_log_repository: AuditLogRepository):
        super().__init__(audit_log_repository)
        self.audit_log_repository = audit_log_repository

    def list_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        offset = (page - 1) * page_size
        items = self.audit_log_repository.list_logs(
            user_id=user_id,
            action=action,
            offset=offset,
            limit=page_size,
        )

        filters = {}
        if user_id is not None:
            filters["user_id"] = user_id
        if action:
            filters["action"] = action

        total_count = self.audit_log_repository.count(filters=filters)
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
