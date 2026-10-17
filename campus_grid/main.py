from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from campus_grid.api.v1.routes import routers as v1_routers
from campus_grid.core.config import configs
from campus_grid.core.container import Container
from campus_grid.util.class_object import singleton


@singleton
class AppCreator:
    def __init__(self) -> None:
        self.app = FastAPI(
            title=f"{configs.PROJECT_NAME} API",
            description="Enterprise Asset & Facility Reservation Engine featuring Clean Architecture, strict RBAC, and transactional double-booking prevention.",
            version="1.0.0",
            openapi_url=f"{configs.API}/openapi.json",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # Initialize DI Container
        self.container = Container()
        self.container.wire(
            modules=[
                "campus_grid.api.v1.endpoints.auth",
                "campus_grid.api.v1.endpoints.user",
                "campus_grid.api.v1.endpoints.resource",
                "campus_grid.api.v1.endpoints.booking",
                "campus_grid.api.v1.endpoints.audit_log",
                "campus_grid.core.dependencies",
            ]
        )
        self.db = self.container.db()

        # Auto-create tables for development/testing if database is fresh
        self.db.create_database()

        # Configure CORS
        if configs.BACKEND_CORS_ORIGINS:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=[str(origin) for origin in configs.BACKEND_CORS_ORIGINS],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        # Health & Root Endpoints
        @self.app.get("/", tags=["Health"])
        def root():
            return {
                "name": configs.PROJECT_NAME,
                "status": "online",
                "version": "1.0.0",
                "docs": "/docs",
            }

        @self.app.get("/health", tags=["Health"])
        def health_check():
            return {"status": "healthy", "environment": configs.ENV}

        # Include API v1 routers
        self.app.include_router(v1_routers, prefix=configs.API_V1_STR)


app_creator = AppCreator()
app = app_creator.app
db = app_creator.db
container = app_creator.container
