import math
from typing import Dict, Any

from campus_grid.core.exceptions import NotFoundError
from campus_grid.model.user import User
from campus_grid.repository.audit_log_repository import AuditLogRepository
from campus_grid.repository.user_repository import UserRepository
from campus_grid.schema.user_schema import UserRoleUpdate
from campus_grid.services.base_service import BaseService


class UserService(BaseService[User]):
    def __init__(self, user_repository: UserRepository, audit_log_repository: AuditLogRepository):
        super().__init__(user_repository)
        self.user_repository = user_repository
        self.audit_log_repository = audit_log_repository

    def list_users(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        offset = (page - 1) * page_size
        items = self.user_repository.list(offset=offset, limit=page_size)
        total_count = self.user_repository.count()
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def update_user_status_or_role(self, user_id: int, updates: UserRoleUpdate, admin_user: User) -> User:
        user = self.user_repository.get_by_id_or_raise(user_id)
        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            return user

        updated_user = self.user_repository.update(user_id, update_data)
        if not updated_user:
            raise NotFoundError(detail=f"User with ID {user_id} not found")

        with self.user_repository.session_factory() as session:
            self.audit_log_repository.log(
                session=session,
                user_id=admin_user.id,
                action="USER_ROLE_UPDATED",
                meta_data={"target_user_id": user_id, "changes": update_data},
            )
            session.commit()

        return updated_user
