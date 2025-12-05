"""API routes for Notifications Service."""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from . import __version__
from .channels import CHANNELS, check_channel_health, send_notification
from .config import settings
from .database import get_db, get_notification_history, store_notification
from .models import (
    ChannelInfo,
    ChannelsResponse,
    ChannelType,
    HealthResponse,
    NotificationHistoryItem,
    NotificationHistoryResponse,
    NotificationRequest,
    NotificationResponse,
    NotificationStatus,
    PriorityLevel,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")


@router.post("/notify", response_model=NotificationResponse)
async def notify(
    request: NotificationRequest,
    db: Annotated[Session | None, Depends(get_db)],
):
    """Send a notification via specified channel."""
    logger.info(
        f"Sending {request.priority.value} notification via {request.channel.value}: {request.message[:50]}..."
    )

    # Send notification
    status, error = await send_notification(
        channel_type=request.channel,
        message=request.message,
        priority=request.priority,
        metadata=request.metadata,
        recipient=request.recipient,
    )

    # Store in database (if available)
    notification_id = None
    if db:
        notification_id = store_notification(
            db=db,
            channel=request.channel,
            message=request.message,
            priority=request.priority,
            status=status,
            notification_metadata=request.metadata,
            recipient=request.recipient,
            error=error,
        )
    else:
        # Generate ID without database
        import uuid

        notification_id = str(uuid.uuid4())
        logger.debug("Database not configured - skipping history storage")

    if status == NotificationStatus.FAILED:
        logger.error(f"Notification {notification_id} failed: {error}")
    else:
        logger.info(f"Notification {notification_id} sent successfully")

    return NotificationResponse(
        notification_id=notification_id,
        status=status,
        channel=request.channel,
        sent_at=datetime.utcnow(),
        error=error,
    )


@router.get("/channels", response_model=ChannelsResponse)
async def list_channels():
    """List all notification channels and their status."""
    channels = []

    for channel_type, channel_instance in CHANNELS.items():
        # Check channel health
        is_healthy, error = await check_channel_health(channel_type)

        channels.append(
            ChannelInfo(
                name=channel_type,
                enabled=channel_instance.enabled,
                status="healthy" if is_healthy else "unhealthy",
                configured=channel_instance.enabled,
                error=error,
            )
        )

    return ChannelsResponse(channels=channels)


@router.get("/history", response_model=NotificationHistoryResponse)
async def get_history(
    db: Annotated[Session | None, Depends(get_db)],
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    channel: ChannelType | None = None,
    status: NotificationStatus | None = None,
    priority: PriorityLevel | None = None,
    service: str | None = None,
):
    """Get notification history with optional filters."""
    if not db:
        raise HTTPException(
            status_code=503, detail="Database not configured - history not available"
        )

    records, total = get_notification_history(
        db=db,
        limit=limit,
        offset=offset,
        channel=channel,
        status=status,
        priority=priority,
        service=service,
    )

    notifications = [
        NotificationHistoryItem(
            id=record.id,
            channel=record.channel,
            message=record.message,
            priority=record.priority,
            status=record.status,
            sent_at=record.sent_at,
            metadata=record.notification_metadata,
            error=record.error,
        )
        for record in records
    ]

    return NotificationHistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        notifications=notifications,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    # Check all channels
    channel_health = {}
    for channel_type in CHANNELS.keys():
        is_healthy, _ = await check_channel_health(channel_type)
        channel_health[channel_type.value] = "healthy" if is_healthy else "unhealthy"

    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=__version__,
        timestamp=datetime.utcnow(),
        channels=channel_health,
    )
