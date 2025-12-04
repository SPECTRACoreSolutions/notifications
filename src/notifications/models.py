"""Data models for Notifications Service."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    """Supported notification channels."""

    DISCORD = "discord"
    EMAIL = "email"
    TEAMS = "teams"
    SMS = "sms"
    STDOUT = "stdout"


class PriorityLevel(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationRequest(BaseModel):
    """Request to send a notification."""

    channel: ChannelType = Field(..., description="Notification channel")
    message: str = Field(..., min_length=1, max_length=4096, description="Notification message")
    priority: PriorityLevel = Field(
        default=PriorityLevel.NORMAL, description="Notification priority"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata (service, error, etc.)"
    )
    recipient: str | None = Field(
        default=None, description="Recipient (email address, phone number, etc.)"
    )


class NotificationResponse(BaseModel):
    """Response from sending a notification."""

    notification_id: str = Field(..., description="Unique notification ID")
    status: NotificationStatus = Field(..., description="Delivery status")
    channel: ChannelType = Field(..., description="Channel used")
    sent_at: datetime = Field(..., description="Timestamp when sent")
    error: str | None = Field(default=None, description="Error message if failed")


class ChannelInfo(BaseModel):
    """Information about a notification channel."""

    name: ChannelType = Field(..., description="Channel name")
    enabled: bool = Field(..., description="Whether channel is enabled")
    status: str = Field(..., description="Channel health status")
    configured: bool = Field(..., description="Whether channel is properly configured")
    error: str | None = Field(default=None, description="Configuration error if any")


class ChannelsResponse(BaseModel):
    """Response listing all channels."""

    channels: list[ChannelInfo] = Field(..., description="List of channels")


class NotificationHistoryItem(BaseModel):
    """Historical notification record."""

    id: str = Field(..., description="Notification ID")
    channel: ChannelType = Field(..., description="Channel used")
    message: str = Field(..., description="Message sent")
    priority: PriorityLevel = Field(..., description="Priority level")
    status: NotificationStatus = Field(..., description="Delivery status")
    sent_at: datetime = Field(..., description="Timestamp when sent")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")
    error: str | None = Field(default=None, description="Error if failed")


class NotificationHistoryResponse(BaseModel):
    """Response with notification history."""

    total: int = Field(..., description="Total matching notifications")
    limit: int = Field(..., description="Result limit")
    offset: int = Field(..., description="Result offset")
    notifications: list[NotificationHistoryItem] = Field(..., description="Notification records")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Current timestamp")
    channels: dict[str, str] = Field(
        default_factory=dict, description="Channel health status"
    )

