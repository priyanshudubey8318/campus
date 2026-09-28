"""Health check endpoints for CampusPulse API."""

import time
from datetime import datetime, timezone
from fastapi import APIRouter, status
from app.core.config import get_settings
from app.core.database import check_database_connection
from app.schemas.health import HealthResponse, DatabaseHealthResponse, DatabaseHealth

router = APIRouter()
settings = get_settings()

START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application and Database Health Check",
    description="Returns application status, version, uptime, and database connectivity.",
)
def get_system_health() -> HealthResponse:
    """Perform system and database health check."""
    db_check = check_database_connection()
    uptime = time.time() - START_TIME

    system_status = "healthy" if db_check["connected"] else "degraded"

    return HealthResponse(
        status=system_status,
        app_name=settings.APP_NAME,
        version="0.1.0",
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=round(uptime, 2),
        database=DatabaseHealth(
            connected=db_check["connected"],
            dialect=db_check["dialect"],
            message=db_check["message"],
        ),
    )


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Dedicated Database Health Check",
    description="Performs an isolated ping test against the configured database engine.",
)
def get_database_health() -> DatabaseHealthResponse:
    """Perform dedicated database ping check."""
    db_check = check_database_connection()
    status_text = "healthy" if db_check["connected"] else "unavailable"

    return DatabaseHealthResponse(
        status=status_text,
        database=DatabaseHealth(
            connected=db_check["connected"],
            dialect=db_check["dialect"],
            message=db_check["message"],
        ),
        timestamp=datetime.now(timezone.utc),
    )
