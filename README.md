# SPECTRA Notifications Service

Multi-channel outbound notification sender for SPECTRA platform.

## Features

- Discord webhook integration
- Slack integration
- Teams integration
- SMS via Twilio
- Email via SendGrid
- Priority-based routing

## Usage

```python
import httpx

response = httpx.post(
    "https://notifications-production.up.railway.app/api/v1/send",
    json={
        "channel": "discord",
        "message": "Hello from SPECTRA!",
        "priority": "INFO"
    }
)
```

## Environment Variables

- `DISCORD_WEBHOOK_URL` - Discord webhook URL for alerts
- `SLACK_WEBHOOK_URL` - Slack webhook URL (optional)
- `TEAMS_WEBHOOK_URL` - Teams webhook URL (optional)

## Health Check

```
GET /health
```

## API Documentation

```
GET /docs
```
