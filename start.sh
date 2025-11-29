#!/usr/bin/env bash
set -e

# Hugging Face provides PORT; default to 7860 locally
export PORT="${PORT:-7860}"

# Locate PostgreSQL binaries (initdb/pg_ctl) even on versioned paths
PG_BIN=$(dirname $(find /usr/lib/postgresql -name initdb | head -n 1 2>/dev/null))
if [ -n "$PG_BIN" ]; then
  export PATH="$PG_BIN:$PATH"
fi

# Normalize DB host: if set to 'db' (compose style), force localhost for single-container run
if [ "${POSTGRES_HOST}" = "db" ] || [ "${POSTGRES_HOST}" = "\"db\"" ] || [ -z "${POSTGRES_HOST}" ]; then
  export POSTGRES_HOST="127.0.0.1"
fi
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_USER="${POSTGRES_USER:-agentic_user}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-password123}"
export POSTGRES_DB="${POSTGRES_DB:-agentic_hr}"

echo "[start.sh] PORT=${PORT}"
echo "[start.sh] POSTGRES_HOST=${POSTGRES_HOST}"
echo "[start.sh] POSTGRES_PORT=${POSTGRES_PORT}"
echo "[start.sh] POSTGRES_USER=${POSTGRES_USER}"
echo "[start.sh] POSTGRES_DB=${POSTGRES_DB}"

# Start local Postgres if not already running
export PGDATA=/var/lib/postgresql/data
mkdir -p "$PGDATA"
chown -R postgres:postgres "$PGDATA"
mkdir -p /var/run/postgresql
chown postgres:postgres /var/run/postgresql

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  echo "[start.sh] Initializing postgres data dir..."
  gosu postgres initdb -D "$PGDATA"
fi

echo "[start.sh] Starting postgres on port ${POSTGRES_PORT}..."
if ! gosu postgres pg_ctl -D "$PGDATA" -o "-p ${POSTGRES_PORT} -k /var/run/postgresql" -w start >> /var/log/postgres.log 2>&1; then
  echo "[start.sh] Postgres failed to start. Last log lines:"
  tail -n 100 /var/log/postgres.log || true
  exit 1
fi
echo "[start.sh] Postgres started."
echo "[start.sh] Postgres last log lines:"
tail -n 50 /var/log/postgres.log || true

# Ensure user/db exist
gosu postgres psql -h 127.0.0.1 -p "${POSTGRES_PORT}" -v ON_ERROR_STOP=1 --command "DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_USER}') THEN
      CREATE ROLE ${POSTGRES_USER} LOGIN PASSWORD '${POSTGRES_PASSWORD}';
   END IF;
END
\$\$;" || true
gosu postgres psql -h 127.0.0.1 -p "${POSTGRES_PORT}" -v ON_ERROR_STOP=1 --command "CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER}" || true
echo "[start.sh] Postgres user/db ensured."

# Create tables if they don't exist
echo "[start.sh] Ensuring database tables exist..."
python - <<'PY'
import os
from src.database.candidates.models import Base
from src.database.candidates.client import engine

try:
    Base.metadata.create_all(bind=engine)
    print("[db-init] Tables ensured.")
except Exception as e:
    print(f"[db-init] Failed to create tables: {e}")
PY

# Defaults for local in-container routing; can be overridden via env
export SUPERVISOR_API_URL="${SUPERVISOR_API_URL:-http://127.0.0.1:8080/api/v1/supervisor}"
export DATABASE_API_URL="${DATABASE_API_URL:-http://127.0.0.1:8080/api/v1/db}"
export CV_UPLOAD_API_URL="${CV_UPLOAD_API_URL:-http://127.0.0.1:8080/api/v1/cv}"

# Start FastAPI backend
uvicorn src.api.app:app --host 0.0.0.0 --port 8080 &

# Give the API a moment to come up
sleep 2

# Run Gradio frontend
python src/frontend/gradio/app.py
