"""Pydantic schemas for application and database health checks."""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    """Database connectivity details."""
    connected: bool = Field(..., description="Whether database connection succeeded")
    dialect: str = Field(..., description="SQLAlchemy dialect in use")
    message: str = Field(..., description="Status message or error detail")


class HealthResponse(BaseModel):
    """Primary system health check response contract."""
    status: str = Field(..., description="Overall system health status (healthy, degraded)")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Semantic software version")
    environment: str = Field(..., description="Active environment (development, staging, production)")
    timestamp: datetime = Field(..., description="Current server UTC timestamp")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    database: DatabaseHealth = Field(..., description="Database connectivity status")


class DatabaseHealthResponse(BaseModel):
    """Dedicated database health check response contract."""
    status: str = Field(..., description="Database status (healthy, unavailable)")
    database: DatabaseHealth = Field(..., description="Database connectivity details")
    timestamp: datetime = Field(..., description="Current server UTC timestamp")
