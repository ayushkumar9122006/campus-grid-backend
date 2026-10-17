import math
from typing import Any, Dict, Optional

from campus_grid.core.exceptions import NotFoundError
from campus_grid.model.resource import Resource, ResourceStatus
from campus_grid.model.user import User
from campus_grid.repository.audit_log_repository import AuditLogRepository
from campus_grid.repository.resource_repository import ResourceRepository
from campus_grid.schema.resource_schema import ResourceCreate, ResourceUpdate
from campus_grid.services.base_service import BaseService


class ResourceService(BaseService[Resource]):
    def __init__(self, resource_repository: ResourceRepository, audit_log_repository: AuditLogRepository):
        super().__init__(resource_repository)
        self.resource_repository = resource_repository
        self.audit_log_repository = audit_log_repository

    def create_resource(self, resource_in: ResourceCreate, actor_user: User) -> Resource:
        resource = Resource(
            name=resource_in.name,
            category=resource_in.category,
            total_quantity=resource_in.total_quantity,
            available_quantity=resource_in.available_quantity or resource_in.total_quantity,
            status=resource_in.status,
        )

        with self.resource_repository.session_factory() as session:
            session.add(resource)
            session.flush()
            self.audit_log_repository.log(
                session=session,
                user_id=actor_user.id,
                action="RESOURCE_CREATED",
                meta_data={
                    "resource_id": resource.id,
                    "name": resource.name,
                    "category": resource.category,
                    "total_quantity": resource.total_quantity,
                },
            )
            session.commit()
            session.refresh(resource)
            return resource

    def list_resources(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        offset = (page - 1) * page_size
        items = self.resource_repository.list_resources(
            category=category,
            status=status,
            offset=offset,
            limit=page_size,
        )
        filters = {}
        if category:
            filters["category"] = category
        if status:
            filters["status"] = status
        total_count = self.resource_repository.count(filters=filters)
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def update_resource(self, resource_id: int, resource_in: ResourceUpdate, actor_user: User) -> Resource:
        resource = self.resource_repository.get_by_id_or_raise(resource_id)
        update_data = resource_in.model_dump(exclude_unset=True)
        if not update_data:
            return resource

        updated = self.resource_repository.update(resource_id, update_data)
        if not updated:
            raise NotFoundError(detail=f"Resource with ID {resource_id} not found")

        with self.resource_repository.session_factory() as session:
            self.audit_log_repository.log(
                session=session,
                user_id=actor_user.id,
                action="RESOURCE_UPDATED",
                meta_data={"resource_id": resource_id, "changes": update_data},
            )
            session.commit()

        return updated

    def delete_resource(self, resource_id: int, actor_user: User) -> bool:
        resource = self.resource_repository.get_by_id_or_raise(resource_id)
        success = self.resource_repository.delete(resource_id)

        with self.resource_repository.session_factory() as session:
            self.audit_log_repository.log(
                session=session,
                user_id=actor_user.id,
                action="RESOURCE_DELETED",
                meta_data={"resource_id": resource_id, "name": resource.name},
            )
            session.commit()

        return success
