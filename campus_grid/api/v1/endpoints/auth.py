from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from campus_grid.core.container import Container
from campus_grid.core.dependencies import get_current_active_user
from campus_grid.model.user import User
from campus_grid.schema.auth_schema import TokenResponse
from campus_grid.schema.user_schema import UserLogin, UserRegister, UserResponse
from campus_grid.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/sign-up", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@inject
def sign_up(
    user_info: UserRegister,
    service: AuthService = Depends(Provide[Container.auth_service]),
):
    """Register a new student, faculty member, or campus administrator."""
    return service.sign_up(user_info)


@router.post("/sign-in", response_model=TokenResponse)
@inject
def sign_in(
    login_info: UserLogin,
    service: AuthService = Depends(Provide[Container.auth_service]),
):
    """Authenticate with credentials and obtain a JWT access token."""
    return service.sign_in(login_info)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Retrieve profile and role information for the authenticated user."""
    return current_user
