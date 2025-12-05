"""Unit tests for notification models."""

import pytest
from datetime import datetime
from notifications.models import (
    ChannelType,
    PriorityLevel,
    NotificationStatus,
    NotificationRequest,
    NotificationResponse,
    ChannelInfo,
)


def test_channel_type_enum():
    """Test ChannelType enum values."""
    assert ChannelType.DISCORD == "discord"
    assert ChannelType.EMAIL == "email"
    assert ChannelType.TEAMS == "teams"
    assert ChannelType.SMS == "sms"
    assert ChannelType.STDOUT == "stdout"


def test_priority_level_enum():
    """Test PriorityLevel enum values."""
    assert PriorityLevel.LOW == "low"
    assert PriorityLevel.NORMAL == "normal"
    assert PriorityLevel.HIGH == "high"
    assert PriorityLevel.CRITICAL == "critical"


def test_notification_status_enum():
    """Test NotificationStatus enum values."""
    assert NotificationStatus.PENDING == "pending"
    assert NotificationStatus.SENT == "sent"
    assert NotificationStatus.DELIVERED == "delivered"
    assert NotificationStatus.FAILED == "failed"


def test_notification_request_valid():
    """Test creating valid NotificationRequest."""
    request = NotificationRequest(
        channel=ChannelType.DISCORD,
        message="Test alert",
        priority=PriorityLevel.HIGH,
        metadata={"service": "test-service", "error": "test error"},
    )
    
    assert request.channel == ChannelType.DISCORD
    assert request.message == "Test alert"
    assert request.priority == PriorityLevel.HIGH
    assert request.metadata["service"] == "test-service"
    assert request.recipient is None


def test_notification_request_with_recipient():
    """Test NotificationRequest with recipient."""
    request = NotificationRequest(
        channel=ChannelType.EMAIL,
        message="Test email",
        recipient="test@example.com",
    )
    
    assert request.channel == ChannelType.EMAIL
    assert request.recipient == "test@example.com"
    assert request.priority == PriorityLevel.NORMAL  # Default


def test_notification_request_defaults():
    """Test NotificationRequest default values."""
    request = NotificationRequest(
        channel=ChannelType.STDOUT,
        message="Test message",
    )
    
    assert request.priority == PriorityLevel.NORMAL
    assert request.metadata == {}
    assert request.recipient is None


def test_notification_request_validation():
    """Test NotificationRequest validation."""
    # Message too short
    with pytest.raises(ValueError):
        NotificationRequest(
            channel=ChannelType.DISCORD,
            message="",  # Empty message should fail
        )
    
    # Message too long
    with pytest.raises(ValueError):
        NotificationRequest(
            channel=ChannelType.DISCORD,
            message="x" * 5000,  # Over 4096 limit
        )


def test_notification_response():
    """Test NotificationResponse model."""
    response = NotificationResponse(
        notification_id="test-123",
        status=NotificationStatus.DELIVERED,
        channel=ChannelType.DISCORD,
        sent_at=datetime.utcnow(),
        error=None,
    )
    
    assert response.notification_id == "test-123"
    assert response.status == NotificationStatus.DELIVERED
    assert response.channel == ChannelType.DISCORD
    assert response.error is None


def test_notification_response_with_error():
    """Test NotificationResponse with error."""
    response = NotificationResponse(
        notification_id="test-456",
        status=NotificationStatus.FAILED,
        channel=ChannelType.EMAIL,
        sent_at=datetime.utcnow(),
        error="SMTP connection failed",
    )
    
    assert response.status == NotificationStatus.FAILED
    assert response.error == "SMTP connection failed"


def test_channel_info():
    """Test ChannelInfo model."""
    info = ChannelInfo(
        name=ChannelType.DISCORD,
        enabled=True,
        status="healthy",
        configured=True,
        error=None,
    )
    
    assert info.name == ChannelType.DISCORD
    assert info.enabled is True
    assert info.status == "healthy"
    assert info.configured is True


def test_channel_info_unhealthy():
    """Test ChannelInfo for unhealthy channel."""
    info = ChannelInfo(
        name=ChannelType.EMAIL,
        enabled=False,
        status="unhealthy",
        configured=False,
        error="SMTP credentials not configured",
    )
    
    assert info.enabled is False
    assert info.status == "unhealthy"
    assert info.error == "SMTP credentials not configured"

