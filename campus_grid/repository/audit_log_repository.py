from contextlib import AbstractContextManager
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from campus_grid.model.audit_log import AuditLog
from campus_grid.repository.base_repository import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        super().__init__(session_factory, AuditLog)

    def log(
        self,
        session: Session,
        user_id: Optional[int],
        action: str,
        meta_data: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create an audit log record within the provided transaction context."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            meta_data=meta_data,
        )
        session.add(entry)
        return entry

    def list_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[AuditLog]:
        with self.session_factory() as session:
            stmt = select(AuditLog)
            if user_id is not None:
                stmt = stmt.where(AuditLog.user_id == user_id)
            if action:
                stmt = stmt.where(AuditLog.action == action)
            stmt = stmt.order_by(AuditLog.id.desc()).offset(offset).limit(limit)
            return list(session.scalars(stmt).all())
