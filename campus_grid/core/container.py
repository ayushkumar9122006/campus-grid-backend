from dependency_injector import containers, providers

from campus_grid.core.config import configs
from campus_grid.core.database import Database
from campus_grid.repository.audit_log_repository import AuditLogRepository
from campus_grid.repository.booking_repository import BookingRepository
from campus_grid.repository.resource_repository import ResourceRepository
from campus_grid.repository.user_repository import UserRepository
from campus_grid.services.audit_log_service import AuditLogService
from campus_grid.services.auth_service import AuthService
from campus_grid.services.booking_service import BookingService
from campus_grid.services.resource_service import ResourceService
from campus_grid.services.user_service import UserService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "campus_grid.api.v1.endpoints.auth",
            "campus_grid.api.v1.endpoints.user",
            "campus_grid.api.v1.endpoints.resource",
            "campus_grid.api.v1.endpoints.booking",
            "campus_grid.api.v1.endpoints.audit_log",
            "campus_grid.core.dependencies",
        ]
    )

    db = providers.Singleton(Database, db_url=configs.DATABASE_URI)

    # Repositories
    user_repository = providers.Factory(UserRepository, session_factory=db.provided.session)
    resource_repository = providers.Factory(ResourceRepository, session_factory=db.provided.session)
    booking_repository = providers.Factory(BookingRepository, session_factory=db.provided.session)
    audit_log_repository = providers.Factory(AuditLogRepository, session_factory=db.provided.session)

    # Services
    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository,
        audit_log_repository=audit_log_repository,
    )
    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
        audit_log_repository=audit_log_repository,
    )
    resource_service = providers.Factory(
        ResourceService,
        resource_repository=resource_repository,
        audit_log_repository=audit_log_repository,
    )
    booking_service = providers.Factory(
        BookingService,
        booking_repository=booking_repository,
        resource_repository=resource_repository,
        audit_log_repository=audit_log_repository,
        session_factory=db.provided.session,
    )
    audit_log_service = providers.Factory(
        AuditLogService,
        audit_log_repository=audit_log_repository,
    )
