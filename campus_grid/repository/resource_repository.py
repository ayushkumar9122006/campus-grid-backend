from contextlib import AbstractContextManager
from typing import Callable, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from campus_grid.model.resource import Resource
from campus_grid.repository.base_repository import BaseRepository


class ResourceRepository(BaseRepository[Resource]):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        super().__init__(session_factory, Resource)

    def get_by_id_locked(self, session: Session, resource_id: int) -> Optional[Resource]:
        """Fetch resource with pessimistic row-level lock for transactional concurrency."""
        stmt = select(Resource).where(Resource.id == resource_id)
        bind = session.get_bind()
        if bind and bind.dialect.name != "sqlite":
            stmt = stmt.with_for_update()
        return session.scalar(stmt)

    def list_resources(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Resource]:
        filters = {}
        if category:
            filters["category"] = category
        if status:
            filters["status"] = status
        return self.list(offset=offset, limit=limit, filters=filters)
