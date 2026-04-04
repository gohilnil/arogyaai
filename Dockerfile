# ── Build stage ────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps into a local dir for copying to final image
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Final stage ────────────────────────────────────────────────────
FROM python:3.11-slim

LABEL maintainer="ArogyaAI <dev@arogyaai.in>"
LABEL version="3.0.0"
LABEL description="ArogyaAI — India's AI Health Companion"

# Security: minimal attack surface
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy only the installed packages from builder
COPY --from=builder /install /usr/local

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PORT=8000 \
    APP_ENV=production

WORKDIR /app

# Copy application code (no .env, no venv, no tests)
COPY backend/main.py ./backend/
COPY backend/app/ ./backend/app/
COPY backend/requirements.txt ./backend/
COPY frontend/ ./frontend/

# Non-root user for security
RUN useradd -m -u 1001 -s /bin/sh arogyaai && \
    chown -R arogyaai:arogyaai /app
USER arogyaai

WORKDIR /app/backend

EXPOSE 8000

# Health check — fails fast if app is broken
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production: Uvicorn with multiple workers
# Increase --workers to match your CPU count on the host
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info", \
     "--access-log", \
     "--no-server-header"]
