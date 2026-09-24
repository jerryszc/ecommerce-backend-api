#!/bin/sh
# Entrypoint compatible local/Render: migra y sirve en $PORT.
# Render inyecta PORT (default 10000); docker-compose/local usan 8000.
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
