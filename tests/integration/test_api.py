"""Integration tests for Notifications API."""

import pytest
from fastapi.testclient import TestClient
from notifications.main import app
from notifications.models import ChannelType, PriorityLevel


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns service info."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "notifications"
    assert data["status"] == "operational"
    assert "version" in data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "notifications"
    assert "version" in data


def test_v1_health_endpoint(client):
    """Test v1 health check endpoint."""
    response = client.get("/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "channels" in data


def test_list_channels(client):
    """Test listing notification channels."""
    response = client.get("/v1/channels")
    
    assert response.status_code == 200
    data = response.json()
    assert "channels" in data
    assert len(data["channels"]) > 0
    
    # Verify channel structure
    channel = data["channels"][0]
    assert "name" in channel
    assert "enabled" in channel
    assert "status" in channel


def test_send_notification_stdout(client):
    """Test sending notification to stdout (always enabled)."""
    response = client.post(
        "/v1/notify",
        json={
            "channel": "stdout",
            "message": "Test notification",
            "priority": "normal",
            "metadata": {"test": "true"},
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "notification_id" in data
    assert data["channel"] == "stdout"
    assert data["status"] in ["sent", "delivered"]


def test_send_notification_missing_channel(client):
    """Test sending notification without channel."""
    response = client.post(
        "/v1/notify",
        json={
            "message": "Test notification",
        },
    )
    
    assert response.status_code == 422  # Validation error


def test_send_notification_missing_message(client):
    """Test sending notification without message."""
    response = client.post(
        "/v1/notify",
        json={
            "channel": "stdout",
        },
    )
    
    assert response.status_code == 422  # Validation error


def test_send_notification_invalid_channel(client):
    """Test sending notification to invalid channel."""
    response = client.post(
        "/v1/notify",
        json={
            "channel": "invalid_channel",
            "message": "Test",
        },
    )
    
    assert response.status_code == 422  # Validation error


def test_send_notification_invalid_priority(client):
    """Test sending notification with invalid priority."""
    response = client.post(
        "/v1/notify",
        json={
            "channel": "stdout",
            "message": "Test",
            "priority": "invalid_priority",
        },
    )
    
    assert response.status_code == 422  # Validation error


def test_send_notification_all_priorities(client):
    """Test sending notifications with all priority levels."""
    priorities = ["low", "normal", "high", "critical"]
    
    for priority in priorities:
        response = client.post(
            "/v1/notify",
            json={
                "channel": "stdout",
                "message": f"Test {priority} alert",
                "priority": priority,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["sent", "delivered"]


def test_notification_history(client):
    """Test getting notification history (requires database)."""
    # Send a notification first
    client.post(
        "/v1/notify",
        json={
            "channel": "stdout",
            "message": "History test",
            "priority": "normal",
        },
    )
    
    # Get history
    response = client.get("/v1/history")
    
    # Should return 200 or 503 (if database not configured)
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "notifications" in data
        assert "total" in data


def test_api_docs_available(client):
    """Test that API documentation is available."""
    response = client.get("/docs")
    
    assert response.status_code == 200


def test_openapi_schema_available(client):
    """Test that OpenAPI schema is available."""
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "SPECTRA Notifications Service"

