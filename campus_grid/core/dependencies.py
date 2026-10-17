from typing import Callable, List
from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from jose import jwt

from campus_grid.core.config import configs
from campus_grid.core.container import Container
from campus_grid.core.exceptions import AuthError, PermissionDeniedError
from campus_grid.core.security import ALGORITHM, JWTBearer
from campus_grid.model.user import User, UserRole
from campus_grid.services.user_service import UserService


@inject
def get_current_user(
    token: str = Depends(JWTBearer()),
    user_service: UserService = Depends(Provide[Container.user_service]),
) -> User:
    try:
        payload = jwt.decode(token, configs.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthError(detail="Invalid token payload: missing subject")
        user_id = int(user_id_str)
    except Exception:
        raise AuthError(detail="Could not validate credentials")

    try:
        user: User = user_service.get_by_id(user_id)
    except Exception:
        raise AuthError(detail="User record not found")

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise AuthError(detail="User account is inactive")
    return current_user


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    """Dependency factory generating role-based permission gates."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            role_names = ", ".join([r.value for r in allowed_roles])
            raise PermissionDeniedError(
                detail=f"Operation restricted to roles [{role_names}]. Current role: '{current_user.role.value}'."
            )
        return current_user

    return role_checker


# Explicit Role Dependencies
require_admin = require_roles(UserRole.ADMIN)
require_faculty_or_admin = require_roles(UserRole.FACULTY, UserRole.ADMIN)
require_student = require_roles(UserRole.STUDENT)
