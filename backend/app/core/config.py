"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings model loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env.local", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = Field(default="CampusPulse", description="Application name")
    APP_ENV: str = Field(default="development", description="Runtime environment (development, staging, production)")
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API Version 1 route prefix")

    # Security & Authentication
    SECRET_KEY: str = Field(
        default="dev-insecure-secret-key-replace-in-production-min-32-chars",
        description="Application secret key",
    )
    AUTH_SECRET: str = Field(
        default="campuspulse-dev-jwt-auth-secret-change-in-production-32c",
        description="Secret key for signing JWT tokens",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        description="Access token lifespan in minutes",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token lifespan in days",
    )
    COOKIE_SECURE: bool = Field(
        default=False,
        description="Whether cookies must only be transmitted over HTTPS (automatically enabled in production)",
    )
    COOKIE_SAMESITE: str = Field(
        default="lax",
        description="SameSite cookie policy (lax, strict, none)",
    )
    LOGIN_RATE_LIMIT_ATTEMPTS: int = Field(
        default=5,
        description="Maximum failed login attempts before temporary throttling",
    )
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=300,
        description="Sliding window duration in seconds for login rate limiting",
    )
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/campuspulse",
        description="Primary PostgreSQL database connection string",
    )
    TEST_DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/campuspulse_test",
        description="Isolated PostgreSQL test database connection string",
    )

    # AI & PulseAssist Subsystem
    AI_PROVIDER: str = Field(default="mock", description="AI provider: mock or gemini")
    GEMINI_API_KEY: Union[str, None] = Field(default=None, description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", description="Gemini text generation model")
    GEMINI_EMBEDDING_MODEL: str = Field(default="text-embedding-004", description="Gemini embedding model")


    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    def validate_test_database_safety(self) -> None:
        """Reject test execution if TEST_DATABASE_URL risks mutating production or development data."""
        clean_main = self.DATABASE_URL.strip().lower()
        clean_test = self.TEST_DATABASE_URL.strip().lower()

        if clean_main == clean_test:
            raise ValueError(
                "CRITICAL SAFETY ERROR: TEST_DATABASE_URL cannot be identical to DATABASE_URL. "
                "Tests must use an isolated test database (e.g. campuspulse_test) to protect data integrity."
            )

        # Ensure test database name or schema explicitly identifies as a test database
        if not ("test" in clean_test):
            raise ValueError(
                f"CRITICAL SAFETY ERROR: TEST_DATABASE_URL ({self.TEST_DATABASE_URL}) must contain "
                "'test' in its database name or path to prevent targeting production or development instances."
            )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the settings."""
    return Settings()


settings = get_settings()
