"""Notification channel implementations."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import aiosmtplib
import httpx
from email.message import EmailMessage

from .config import settings
from .models import ChannelType, NotificationStatus, PriorityLevel

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Base class for notification channels."""

    @abstractmethod
    async def send(
        self,
        message: str,
        priority: PriorityLevel,
        metadata: dict[str, Any],
        recipient: str | None = None,
    ) -> tuple[NotificationStatus, str | None]:
        """
        Send notification via this channel.

        Returns:
            (status, error_message) tuple
        """
        pass

    @abstractmethod
    async def health_check(self) -> tuple[bool, str | None]:
        """
        Check if channel is healthy and configured.

        Returns:
            (is_healthy, error_message) tuple
        """
        pass


class DiscordChannel(NotificationChannel):
    """Discord webhook notification channel."""

    def __init__(self):
        self.webhook_url = (
            settings.discord_webhook_url.get_secret_value()
            if settings.discord_webhook_url
            else None
        )
        self.enabled = settings.discord_enabled and self.webhook_url is not None

    def _format_message(
        self, message: str, priority: PriorityLevel, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Format message for Discord webhook."""
        # Priority emoji
        priority_emoji = {
            PriorityLevel.LOW: "ℹ️",
            PriorityLevel.NORMAL: "📢",
            PriorityLevel.HIGH: "⚠️",
            PriorityLevel.CRITICAL: "🚨",
        }

        emoji = priority_emoji.get(priority, "📢")

        # Build embed
        embed = {
            "title": f"{emoji} {priority.value.upper()} Alert",
            "description": message,
            "color": self._get_color(priority),
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [],
        }

        # Add metadata as fields
        for key, value in metadata.items():
            embed["fields"].append({"name": key.replace("_", " ").title(), "value": str(value), "inline": True})

        return {"embeds": [embed]}

    def _get_color(self, priority: PriorityLevel) -> int:
        """Get Discord embed color for priority."""
        colors = {
            PriorityLevel.LOW: 0x3498DB,  # Blue
            PriorityLevel.NORMAL: 0x2ECC71,  # Green
            PriorityLevel.HIGH: 0xF39C12,  # Orange
            PriorityLevel.CRITICAL: 0xE74C3C,  # Red
        }
        return colors.get(priority, 0x95A5A6)  # Gray default

    async def send(
        self,
        message: str,
        priority: PriorityLevel,
        metadata: dict[str, Any],
        recipient: str | None = None,
    ) -> tuple[NotificationStatus, str | None]:
        """Send notification to Discord."""
        if not self.enabled:
            return NotificationStatus.FAILED, "Discord channel not configured"

        try:
            payload = self._format_message(message, priority, metadata)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0,
                )

                if response.status_code in (200, 204):
                    logger.info("Discord notification sent successfully")
                    return NotificationStatus.DELIVERED, None
                else:
                    error_msg = f"Discord webhook returned {response.status_code}"
                    logger.error(error_msg)
                    return NotificationStatus.FAILED, error_msg

        except Exception as e:
            error_msg = f"Discord send failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return NotificationStatus.FAILED, error_msg

    async def health_check(self) -> tuple[bool, str | None]:
        """Check Discord channel health."""
        if not self.enabled:
            return False, "Discord webhook URL not configured"

        try:
            # Send a test GET request to verify webhook exists
            # (Discord webhooks support GET for metadata)
            async with httpx.AsyncClient() as client:
                response = await client.get(self.webhook_url, timeout=5.0)

                if response.status_code == 200:
                    return True, None
                else:
                    return False, f"Webhook returned {response.status_code}"

        except Exception as e:
            return False, f"Health check failed: {str(e)}"


class EmailChannel(NotificationChannel):
    """Email (SMTP) notification channel."""

    def __init__(self):
        self.enabled = settings.email_enabled and settings.smtp_username is not None
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = (
            settings.smtp_password.get_secret_value() if settings.smtp_password else None
        )
        self.from_address = settings.smtp_from_address
        self.use_tls = settings.smtp_use_tls

    async def send(
        self,
        message: str,
        priority: PriorityLevel,
        metadata: dict[str, Any],
        recipient: str | None = None,
    ) -> tuple[NotificationStatus, str | None]:
        """Send notification via email."""
        if not self.enabled:
            return NotificationStatus.FAILED, "Email channel not configured"

        if not recipient:
            return NotificationStatus.FAILED, "Email recipient required"

        try:
            # Create email message
            email = EmailMessage()
            email["From"] = self.from_address
            email["To"] = recipient
            email["Subject"] = f"[{priority.value.upper()}] SPECTRA Alert"

            # Build email body
            body = f"{message}\n\n"
            if metadata:
                body += "Details:\n"
                for key, value in metadata.items():
                    body += f"  {key}: {value}\n"

            email.set_content(body)

            # Send via SMTP
            await aiosmtplib.send(
                email,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=self.use_tls,
                timeout=30.0,
            )

            logger.info(f"Email notification sent to {recipient}")
            return NotificationStatus.DELIVERED, None

        except Exception as e:
            error_msg = f"Email send failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return NotificationStatus.FAILED, error_msg

    async def health_check(self) -> tuple[bool, str | None]:
        """Check email channel health."""
        if not self.enabled:
            return False, "SMTP credentials not configured"

        try:
            # Try to connect to SMTP server
            async with aiosmtplib.SMTP(
                hostname=self.host, port=self.port, timeout=5.0, use_tls=self.use_tls
            ) as smtp:
                await smtp.login(self.username, self.password)
                return True, None

        except Exception as e:
            return False, f"SMTP connection failed: {str(e)}"


class StdoutChannel(NotificationChannel):
    """Console output notification channel (always enabled for logging)."""

    def __init__(self):
        self.enabled = settings.stdout_enabled

    async def send(
        self,
        message: str,
        priority: PriorityLevel,
        metadata: dict[str, Any],
        recipient: str | None = None,
    ) -> tuple[NotificationStatus, str | None]:
        """Send notification to stdout."""
        try:
            # Format for console
            timestamp = datetime.utcnow().isoformat()
            log_line = f"[{timestamp}] [{priority.value.upper()}] {message}"

            if metadata:
                log_line += f" | metadata={metadata}"

            # Log based on priority
            if priority == PriorityLevel.CRITICAL:
                logger.critical(log_line)
            elif priority == PriorityLevel.HIGH:
                logger.warning(log_line)
            else:
                logger.info(log_line)

            return NotificationStatus.DELIVERED, None

        except Exception as e:
            # Stdout should never fail, but handle just in case
            return NotificationStatus.FAILED, f"Stdout write failed: {str(e)}"

    async def health_check(self) -> tuple[bool, str | None]:
        """Check stdout channel health (always healthy)."""
        return True, None


# Channel registry
CHANNELS: dict[ChannelType, NotificationChannel] = {
    ChannelType.DISCORD: DiscordChannel(),
    ChannelType.EMAIL: EmailChannel(),
    ChannelType.STDOUT: StdoutChannel(),
}


async def send_notification(
    channel_type: ChannelType,
    message: str,
    priority: PriorityLevel,
    metadata: dict[str, Any],
    recipient: str | None = None,
    retry_count: int = 0,
) -> tuple[NotificationStatus, str | None]:
    """
    Send notification via specified channel with retry logic.

    Args:
        channel_type: Channel to use
        message: Notification message
        priority: Priority level
        metadata: Additional metadata
        recipient: Recipient (for email/SMS)
        retry_count: Current retry attempt

    Returns:
        (status, error_message) tuple
    """
    channel = CHANNELS.get(channel_type)
    if not channel:
        return NotificationStatus.FAILED, f"Channel {channel_type} not supported"

    # Send notification
    status, error = await channel.send(message, priority, metadata, recipient)

    # Retry logic for failures
    if status == NotificationStatus.FAILED and retry_count < settings.max_retries:
        logger.warning(
            f"Notification failed (attempt {retry_count + 1}/{settings.max_retries}): {error}"
        )
        await asyncio.sleep(settings.retry_delay_seconds)
        return await send_notification(
            channel_type, message, priority, metadata, recipient, retry_count + 1
        )

    return status, error


async def check_channel_health(channel_type: ChannelType) -> tuple[bool, str | None]:
    """Check if channel is healthy."""
    channel = CHANNELS.get(channel_type)
    if not channel:
        return False, "Channel not found"

    return await channel.health_check()

