"""Database models and operations."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Enum, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .config import settings
from .models import ChannelType, NotificationStatus, PriorityLevel

Base = declarative_base()


class NotificationRecord(Base):
    """Database model for notification history."""

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    channel = Column(Enum(ChannelType), nullable=False, index=True)
    message = Column(Text, nullable=False)
    priority = Column(Enum(PriorityLevel), nullable=False, index=True)
    status = Column(Enum(NotificationStatus), nullable=False, index=True)
    recipient = Column(String(255), nullable=True)
    notification_metadata = Column(
        JSON, nullable=False, default=dict
    )  # Renamed from 'metadata' (reserved)
    error = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# Database engine and session (optional)
engine = None
SessionLocal = None

# Only initialize database if URL is configured and not default
if settings.database_url and not settings.database_url.startswith(
    "postgresql://postgres:postgres@localhost"
):
    try:
        engine = create_engine(
            settings.database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        print(f"⚠️  Database not configured: {e}")
        engine = None
        SessionLocal = None


def init_database():
    """Initialize database tables."""
    if engine:
        Base.metadata.create_all(bind=engine)
    else:
        print("⚠️  Skipping database initialization (not configured)")


def get_db() -> Session | None:
    """Get database session (optional)."""
    if not SessionLocal:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def store_notification(
    db: Session,
    channel: ChannelType,
    message: str,
    priority: PriorityLevel,
    status: NotificationStatus,
    notification_metadata: dict[str, Any],
    recipient: str | None = None,
    error: str | None = None,
) -> str:
    """
    Store notification in database.

    Returns:
        notification_id
    """
    notification = NotificationRecord(
        channel=channel,
        message=message,
        priority=priority,
        status=status,
        recipient=recipient,
        notification_metadata=notification_metadata,
        error=error,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification.id


def get_notification_history(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    channel: ChannelType | None = None,
    status: NotificationStatus | None = None,
    priority: PriorityLevel | None = None,
    service: str | None = None,
) -> tuple[list[NotificationRecord], int]:
    """
    Get notification history with filters.

    Returns:
        (records, total_count) tuple
    """
    query = db.query(NotificationRecord)

    # Apply filters
    if channel:
        query = query.filter(NotificationRecord.channel == channel)

    if status:
        query = query.filter(NotificationRecord.status == status)

    if priority:
        query = query.filter(NotificationRecord.priority == priority)

    if service:
        # Filter by service in notification_metadata
        query = query.filter(
            NotificationRecord.notification_metadata["service"].astext == service
        )

    # Get total count
    total = query.count()

    # Apply pagination and order
    records = (
        query.order_by(NotificationRecord.sent_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return records, total
