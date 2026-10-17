import os
from typing import List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Configs(BaseSettings):
    ENV: str = os.getenv("ENV", "dev")
    API: str = "/api"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CampusGrid"

    # Project paths
    PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Date formatting
    DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
    DATE_FORMAT: str = "%Y-%m-%d"

    # Security & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "campusgrid-production-insecure-secret-key-32chars")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Database
    DB: str = os.getenv("DB", "sqlite")
    DB_USER: Optional[str] = os.getenv("DB_USER", None)
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD", None)
    DB_HOST: Optional[str] = os.getenv("DB_HOST", "localhost")
    DB_PORT: Optional[str] = os.getenv("DB_PORT", "5432")
    DB_NAME: Optional[str] = os.getenv("DB_NAME", None)
    DATABASE_URI_OVERRIDE: Optional[str] = os.getenv("DATABASE_URI", os.getenv("DATABASE_URL", None))

    # Pagination Defaults
    PAGE: int = 1
    PAGE_SIZE: int = 20
    ORDERING: str = "-id"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )

    @property
    def DATABASE_URI(self) -> str:
        override = self.DATABASE_URI_OVERRIDE or os.getenv("DATABASE_URL")
        if override:
            if override.startswith("postgres://"):
                override = override.replace("postgres://", "postgresql://", 1)
            return override

        if self.ENV == "test":
            return "sqlite:///:memory:"

        if self.DB == "sqlite":
            return f"sqlite:///{self.PROJECT_ROOT}/campus_grid.db"

        if self.DB == "postgresql":
            db_name = self.DB_NAME or f"campusgrid_{self.ENV}"
            user = self.DB_USER or "postgres"
            password = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
            return f"postgresql://{user}{password}@{self.DB_HOST}:{self.DB_PORT}/{db_name}"

        if self.DB == "mysql":
            db_name = self.DB_NAME or f"campusgrid_{self.ENV}"
            user = self.DB_USER or "root"
            password = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
            return f"mysql+pymysql://{user}{password}@{self.DB_HOST}:{self.DB_PORT}/{db_name}"

        return f"sqlite:///{self.PROJECT_ROOT}/campus_grid.db"


class TestConfigs(Configs):
    ENV: str = "test"


configs = Configs()
if configs.ENV == "test":
    configs = TestConfigs()
