from datetime import timedelta
from typing import Dict, Any

from campus_grid.core.config import configs
from campus_grid.core.exceptions import AuthError, DuplicatedError
from campus_grid.core.security import create_access_token, get_password_hash, verify_password
from campus_grid.model.user import User
from campus_grid.repository.audit_log_repository import AuditLogRepository
from campus_grid.repository.user_repository import UserRepository
from campus_grid.schema.auth_schema import TokenResponse
from campus_grid.schema.user_schema import UserLogin, UserRegister, UserResponse
from campus_grid.services.base_service import BaseService


class AuthService(BaseService[User]):
    def __init__(self, user_repository: UserRepository, audit_log_repository: AuditLogRepository):
        super().__init__(user_repository)
        self.user_repository = user_repository
        self.audit_log_repository = audit_log_repository

    def sign_up(self, user_info: UserRegister) -> User:
        existing = self.user_repository.get_by_email(user_info.email)
        if existing:
            raise DuplicatedError(detail=f"Email '{user_info.email}' is already registered")

        hashed_pwd = get_password_hash(user_info.password)
        user = User(
            email=user_info.email,
            hashed_password=hashed_pwd,
            role=user_info.role,
            is_active=True,
        )

        with self.user_repository.session_factory() as session:
            session.add(user)
            session.flush()
            self.audit_log_repository.log(
                session=session,
                user_id=user.id,
                action="USER_REGISTER",
                meta_data={"email": user.email, "role": user.role.value},
            )
            session.commit()
            session.refresh(user)
            return user

    def sign_in(self, login_info: UserLogin) -> TokenResponse:
        user = self.user_repository.get_by_email(login_info.email)
        if not user:
            raise AuthError(detail="Invalid email or password")

        if not user.is_active:
            raise AuthError(detail="Account is currently inactive")

        if not verify_password(login_info.password, user.hashed_password):
            raise AuthError(detail="Invalid email or password")

        # Create JWT access token
        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
        token_lifespan = timedelta(minutes=configs.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, expiration = create_access_token(token_payload, token_lifespan)

        # Record audit event
        with self.user_repository.session_factory() as session:
            self.audit_log_repository.log(
                session=session,
                user_id=user.id,
                action="USER_LOGIN",
                meta_data={"email": user.email},
            )
            session.commit()

        user_response = UserResponse.model_validate(user)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expiration=expiration,
            user=user_response,
        )
