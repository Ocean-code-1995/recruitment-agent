#!/usr/bin/env bash
set -e

# Hugging Face provides PORT; default to 7860 locally
export PORT="${PORT:-7860}"

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