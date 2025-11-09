from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="The application environment")
    debug: bool = Field(default=False, description="Enable or disable debug mode")

    app_name: str = Field(default="Authentication Service", description="The name of the application")
    app_version: str = Field(default="1.0.0", description="The version of the application")
    app_description: str = Field(
        default="Service for user authentication and management",
        description="The description of the application"
    )
    default_api_version: str = Field(
        default="1.0.0",
        description="The default API version for the application"
    )

    database_url: str = Field(..., description="Database connection URL")
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Maximum overflow size for the database connection pool")
    database_pool_timeout: int = Field(
        default=30,
        description="Timeout for acquiring a database connection from the pool in seconds"
    )

    jwt_secret: str = Field(..., description="Secret key used for JWT token generation")

    enable_api_docs: bool = Field(default=True, description="Enable or disable API documentation endpoints")
    redoc_url: str = Field(default="/redoc", description="URL path for ReDoc documentation")
    docs_url: str = Field(default="/docs", description="URL path for Swagger UI documentation")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8"
    )


    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT


@lru_cache
def get_settings() -> Settings:
    return Settings()  # noqa


settings = get_settings()
