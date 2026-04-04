#!/usr/bin/env bash
# Render start script for ArogyaAI
# Sets PYTHONPATH so uvicorn can find app/ modules relative to backend/
set -e
cd "$(dirname "$0")"
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 2 \
  --log-level info \
  --no-server-header
