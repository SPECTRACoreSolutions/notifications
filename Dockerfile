# SPECTRA Notifications Service Dockerfile

FROM python:3.11-slim

LABEL maintainer="mark@spectra.com"
LABEL service="notifications"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and application code
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 notifications && \
    chown -R notifications:notifications /app

USER notifications

# Expose port (Railway sets PORT dynamically)
EXPOSE ${PORT:-8000}

# Health check (Railway will handle this via their own health check system)
# Using shell form to support $PORT interpolation
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx, os; httpx.get(f'http://localhost:{os.getenv(\"PORT\", \"8000\")}/health', timeout=5.0)" || exit 1

# Start service (use shell form to interpolate PORT)
CMD python -m uvicorn notifications.main:app --host 0.0.0.0 --port ${PORT:-8000}

