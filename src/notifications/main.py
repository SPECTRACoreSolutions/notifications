"""
SPECTRA Notifications Service - FastAPI Application

Multi-channel notification sender for SPECTRA ecosystem.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import settings
from .database import init_database
from .routes import router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("=" * 80)
    logger.info("SPECTRA Notifications Service - Starting Up")
    logger.info("=" * 80)
    logger.info(f"Version: {__version__}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Port: {settings.port}")

    # Initialize database (optional)
    try:
        init_database()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️  Database not available: {e}")
        logger.info("   Notifications will work without history storage")

    # Log channel status
    logger.info("📢 Notification channels:")
    logger.info(f"  Discord: {'✅' if settings.discord_enabled else '❌'}")
    logger.info(f"  Email: {'✅' if settings.email_enabled else '❌'}")
    logger.info(f"  Teams: {'✅' if settings.teams_enabled else '❌'}")
    logger.info(f"  SMS: {'✅' if settings.sms_enabled else '❌'}")
    logger.info(f"  Stdout: {'✅' if settings.stdout_enabled else '❌'}")

    logger.info("🚀 Notifications Service ready!")

    yield

    logger.info("Shutting down Notifications Service...")


# Create FastAPI app
app = FastAPI(
    title="SPECTRA Notifications Service",
    description="Multi-channel notification sender for SPECTRA ecosystem",
    version=__version__,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "notifications",
        "version": __version__,
        "status": "operational",
        "documentation": "/docs",
    }


@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "notifications",
        "version": __version__,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "notifications.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )

