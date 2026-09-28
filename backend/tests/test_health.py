"""Tests for health check endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verify root / endpoint returns API metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "CampusPulse"
    assert data["version"] == "0.1.0"
    assert data["health_url"] == "/api/v1/health"
    assert data["docs_url"] == "/docs"


def test_health_endpoint(client: TestClient):
    """Verify /api/v1/health returns application and database status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "CampusPulse"
    assert data["version"] == "0.1.0"
    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert "database" in data
    assert "connected" in data["database"]
    assert "dialect" in data["database"]


def test_database_health_endpoint(client: TestClient):
    """Verify /api/v1/health/db returns isolated database ping response."""
    response = client.get("/api/v1/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "unavailable"]
    assert "database" in data
    assert "connected" in data["database"]
    assert "dialect" in data["database"]
