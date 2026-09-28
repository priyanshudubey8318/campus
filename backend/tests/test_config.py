"""Tests for configuration management and database safety guards."""

import pytest
from app.core.config import Settings, get_settings


def test_settings_defaults():
    """Verify default configuration values."""
    settings = get_settings()
    assert settings.APP_NAME == "CampusPulse"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert isinstance(settings.ALLOWED_ORIGINS, list)
    assert len(settings.ALLOWED_ORIGINS) > 0
    assert "postgresql://" in settings.DATABASE_URL
    assert "campuspulse_test" in settings.TEST_DATABASE_URL


def test_cors_origins_parsing():
    """Verify comma-separated ALLOWED_ORIGINS string parses into a list."""
    custom_settings = Settings(
        ALLOWED_ORIGINS="http://localhost:3000, https://campus.edu, http://127.0.0.1:3000"
    )
    assert len(custom_settings.ALLOWED_ORIGINS) == 3
    assert "https://campus.edu" in custom_settings.ALLOWED_ORIGINS
    assert "http://localhost:3000" in custom_settings.ALLOWED_ORIGINS


def test_environment_helpers():
    """Verify is_production and is_development properties."""
    dev_settings = Settings(APP_ENV="development")
    assert dev_settings.is_development is True
    assert dev_settings.is_production is False

    prod_settings = Settings(APP_ENV="production")
    assert prod_settings.is_production is True
    assert prod_settings.is_development is False


def test_database_safety_guard_rejects_identical_urls():
    """Guard must reject test execution if TEST_DATABASE_URL is identical to DATABASE_URL."""
    bad_settings = Settings(
        DATABASE_URL="postgresql://postgres:postgres@localhost:5432/campuspulse",
        TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/campuspulse",
    )
    with pytest.raises(ValueError, match="CRITICAL SAFETY ERROR.*cannot be identical"):
        bad_settings.validate_test_database_safety()


def test_database_safety_guard_rejects_non_test_url():
    """Guard must reject test URLs that do not explicitly contain 'test'."""
    unsafe_settings = Settings(
        DATABASE_URL="postgresql://postgres:postgres@localhost:5432/campuspulse_dev",
        TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/campuspulse_live",
    )
    with pytest.raises(ValueError, match="CRITICAL SAFETY ERROR.*must contain 'test'"):
        unsafe_settings.validate_test_database_safety()


def test_database_safety_guard_accepts_valid_isolated_test_url():
    """Guard must allow properly isolated test database URLs."""
    safe_settings = Settings(
        DATABASE_URL="postgresql://postgres:postgres@localhost:5432/campuspulse",
        TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/campuspulse_test",
    )
    # Should not raise
    safe_settings.validate_test_database_safety()
