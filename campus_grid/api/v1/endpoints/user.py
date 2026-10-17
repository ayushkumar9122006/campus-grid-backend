from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from campus_grid.core.container import Container
from campus_grid.core.dependencies import require_admin
from campus_grid.model.user import User
from campus_grid.schema.base_schema import PaginatedResponse
from campus_grid.schema.user_schema import UserResponse, UserRoleUpdate
from campus_grid.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
@inject
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: UserService = Depends(Provide[Container.user_service]),
    current_admin: User = Depends(require_admin),
):
    """List registered users with pagination (Admin only)."""
    return service.list_users(page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserResponse)
@inject
def get_user_detail(
    user_id: int,
    service: UserService = Depends(Provide[Container.user_service]),
    current_admin: User = Depends(require_admin),
):
    """Get single user profile by ID (Admin only)."""
    return service.get_by_id(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
@inject
def update_user_status_or_role(
    user_id: int,
    updates: UserRoleUpdate,
    service: UserService = Depends(Provide[Container.user_service]),
    current_admin: User = Depends(require_admin),
):
    """Update role or active status of a user (Admin only)."""
    return service.update_user_status_or_role(user_id, updates, admin_user=current_admin)
