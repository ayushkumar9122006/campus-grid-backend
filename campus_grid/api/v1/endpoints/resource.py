from typing import Optional
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from campus_grid.core.container import Container
from campus_grid.core.dependencies import get_current_active_user, require_faculty_or_admin
from campus_grid.model.user import User
from campus_grid.schema.base_schema import MessageResponse, PaginatedResponse
from campus_grid.schema.resource_schema import ResourceCreate, ResourceResponse, ResourceUpdate
from campus_grid.services.resource_service import ResourceService

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("", response_model=PaginatedResponse[ResourceResponse])
@inject
def list_resources(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: ResourceService = Depends(Provide[Container.resource_service]),
    current_user: User = Depends(get_current_active_user),
):
    """View campus resource catalog with optional category/status filters (All authenticated users)."""
    return service.list_resources(category=category, status=status, page=page, page_size=page_size)


@router.get("/{resource_id}", response_model=ResourceResponse)
@inject
def get_resource(
    resource_id: int,
    service: ResourceService = Depends(Provide[Container.resource_service]),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve details for a single campus resource."""
    return service.get_by_id(resource_id)


@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
@inject
def create_resource(
    resource_in: ResourceCreate,
    service: ResourceService = Depends(Provide[Container.resource_service]),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Create a new asset, lab equipment, or facility (Faculty & Admin only)."""
    return service.create_resource(resource_in, actor_user=current_user)


@router.put("/{resource_id}", response_model=ResourceResponse)
@inject
def update_resource(
    resource_id: int,
    resource_in: ResourceUpdate,
    service: ResourceService = Depends(Provide[Container.resource_service]),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Update inventory, quantity, or operational status (Faculty & Admin only)."""
    return service.update_resource(resource_id, resource_in, actor_user=current_user)


@router.delete("/{resource_id}", response_model=MessageResponse)
@inject
def delete_resource(
    resource_id: int,
    service: ResourceService = Depends(Provide[Container.resource_service]),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Decommission and remove an asset from the catalog (Faculty & Admin only)."""
    service.delete_resource(resource_id, actor_user=current_user)
    return MessageResponse(message=f"Resource {resource_id} deleted successfully")
