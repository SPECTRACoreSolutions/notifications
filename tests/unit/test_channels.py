"""Unit tests for notification channels."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from notifications.channels import (
    DiscordChannel,
    EmailChannel,
    StdoutChannel,
)
from notifications.models import PriorityLevel, NotificationStatus


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("notifications.channels.settings") as mock:
        mock.discord_enabled = True
        mock.discord_webhook_url = MagicMock()
        mock.discord_webhook_url.get_secret_value.return_value = "https://discord.com/webhook/test"
        
        mock.email_enabled = True
        mock.smtp_host = "smtp.test.com"
        mock.smtp_port = 587
        mock.smtp_username = "test@test.com"
        mock.smtp_password = MagicMock()
        mock.smtp_password.get_secret_value.return_value = "password"
        mock.smtp_from_address = "notifications@spectra.cloud"
        mock.smtp_use_tls = True
        
        mock.stdout_enabled = True
        mock.max_retries = 3
        mock.retry_delay_seconds = 1
        
        yield mock


@pytest.mark.asyncio
async def test_discord_channel_send_success(mock_settings):
    """Test Discord channel sends successfully."""
    channel = DiscordChannel()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        status, error = await channel.send(
            message="Test alert",
            priority=PriorityLevel.HIGH,
            metadata={"service": "test"},
        )
        
        assert status == NotificationStatus.DELIVERED
        assert error is None


@pytest.mark.asyncio
async def test_discord_channel_send_failure(mock_settings):
    """Test Discord channel handles failures."""
    channel = DiscordChannel()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        status, error = await channel.send(
            message="Test alert",
            priority=PriorityLevel.HIGH,
            metadata={},
        )
        
        assert status == NotificationStatus.FAILED
        assert "400" in error


@pytest.mark.asyncio
async def test_discord_channel_not_configured():
    """Test Discord channel when not configured."""
    with patch("notifications.channels.settings") as mock:
        mock.discord_enabled = True
        mock.discord_webhook_url = None
        
        channel = DiscordChannel()
        
        status, error = await channel.send(
            message="Test",
            priority=PriorityLevel.NORMAL,
            metadata={},
        )
        
        assert status == NotificationStatus.FAILED
        assert "not configured" in error


@pytest.mark.asyncio
async def test_discord_health_check_success(mock_settings):
    """Test Discord health check when healthy."""
    channel = DiscordChannel()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        is_healthy, error = await channel.health_check()
        
        assert is_healthy is True
        assert error is None


@pytest.mark.asyncio
async def test_discord_health_check_failure(mock_settings):
    """Test Discord health check when unhealthy."""
    channel = DiscordChannel()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Connection failed")
        )
        
        is_healthy, error = await channel.health_check()
        
        assert is_healthy is False
        assert "failed" in error.lower()


@pytest.mark.asyncio
async def test_email_channel_send_success(mock_settings):
    """Test Email channel sends successfully."""
    channel = EmailChannel()
    
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None
        
        status, error = await channel.send(
            message="Test email",
            priority=PriorityLevel.NORMAL,
            metadata={"service": "test"},
            recipient="test@example.com",
        )
        
        assert status == NotificationStatus.DELIVERED
        assert error is None


@pytest.mark.asyncio
async def test_email_channel_no_recipient():
    """Test Email channel requires recipient."""
    with patch("notifications.channels.settings") as mock:
        mock.email_enabled = True
        mock.smtp_username = "test@test.com"
        
        channel = EmailChannel()
        
        status, error = await channel.send(
            message="Test",
            priority=PriorityLevel.NORMAL,
            metadata={},
            recipient=None,  # No recipient!
        )
        
        assert status == NotificationStatus.FAILED
        assert "recipient required" in error.lower()


@pytest.mark.asyncio
async def test_stdout_channel_always_works():
    """Test Stdout channel always succeeds."""
    channel = StdoutChannel()
    
    status, error = await channel.send(
        message="Test log",
        priority=PriorityLevel.CRITICAL,
        metadata={"test": "data"},
    )
    
    assert status == NotificationStatus.DELIVERED
    assert error is None


@pytest.mark.asyncio
async def test_stdout_health_check():
    """Test Stdout health check always healthy."""
    channel = StdoutChannel()
    
    is_healthy, error = await channel.health_check()
    
    assert is_healthy is True
    assert error is None


def test_discord_message_formatting(mock_settings):
    """Test Discord message formatting."""
    channel = DiscordChannel()
    
    formatted = channel._format_message(
        message="Critical alert!",
        priority=PriorityLevel.CRITICAL,
        metadata={"service": "test-service", "error": "Database down"},
    )
    
    assert "embeds" in formatted
    assert len(formatted["embeds"]) == 1
    
    embed = formatted["embeds"][0]
    assert "CRITICAL" in embed["title"]
    assert embed["description"] == "Critical alert!"
    assert embed["color"] == 0xE74C3C  # Red for critical


def test_discord_color_mapping(mock_settings):
    """Test Discord priority color mapping."""
    channel = DiscordChannel()
    
    assert channel._get_color(PriorityLevel.LOW) == 0x3498DB  # Blue
    assert channel._get_color(PriorityLevel.NORMAL) == 0x2ECC71  # Green
    assert channel._get_color(PriorityLevel.HIGH) == 0xF39C12  # Orange
    assert channel._get_color(PriorityLevel.CRITICAL) == 0xE74C3C  # Red

