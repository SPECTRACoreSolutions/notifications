"""Configuration for Notifications Service."""

import os

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Notifications service configuration."""

    model_config = SettingsConfigDict(
        env_prefix="NOTIFICATIONS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service
    service_name: str = Field(default="notifications", description="Service name")
    environment: str = Field(
        default="development", description="Environment (dev/staging/prod)"
    )
    # Railway uses PORT, allow both PORT and NOTIFICATIONS_PORT
    port: int = Field(default=int(os.getenv("PORT", "8000")), description="HTTP port")
    host: str = Field(default="0.0.0.0", description="HTTP host")
    log_level: str = Field(default="INFO", description="Log level")

    # Database (PostgreSQL)
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/notifications",
        description="PostgreSQL connection URL",
    )

    # Discord Channel
    discord_enabled: bool = Field(
        default=True, description="Enable Discord notifications"
    )
    discord_webhook_url: SecretStr | None = Field(
        default=None, description="Discord webhook URL for alerts"
    )

    # Email Channel (SMTP)
    email_enabled: bool = Field(default=True, description="Enable Email notifications")
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str | None = Field(default=None, description="SMTP username")
    smtp_password: SecretStr | None = Field(default=None, description="SMTP password")
    smtp_from_address: str = Field(
        default="notifications@spectra.cloud", description="From email address"
    )
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")

    # MS Teams Channel
    teams_enabled: bool = Field(
        default=False, description="Enable MS Teams notifications"
    )
    teams_webhook_url: SecretStr | None = Field(
        default=None, description="MS Teams webhook URL"
    )

    # SMS Channel (Twilio)
    sms_enabled: bool = Field(default=False, description="Enable SMS notifications")
    twilio_account_sid: str | None = Field(
        default=None, description="Twilio Account SID"
    )
    twilio_auth_token: SecretStr | None = Field(
        default=None, description="Twilio Auth Token"
    )
    twilio_from_number: str | None = Field(
        default=None, description="Twilio phone number"
    )

    # Stdout Channel (always enabled)
    stdout_enabled: bool = Field(default=True, description="Enable stdout logging")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(
        default=60, description="Max notifications per minute"
    )

    # Retry Configuration
    max_retries: int = Field(
        default=3, description="Max retry attempts for failed notifications"
    )
    retry_delay_seconds: int = Field(default=5, description="Delay between retries")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()


# Global settings instance
settings = Settings()
