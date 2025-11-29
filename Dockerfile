FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirement files
COPY requirements/base.txt requirements/base.txt
COPY requirements/db.txt requirements/db.txt
COPY requirements/agent.txt requirements/agent.txt
COPY requirements/supervisor.txt requirements/supervisor.txt
COPY requirements/api.txt requirements/api.txt
COPY requirements/cv_ui.txt requirements/cv_ui.txt
COPY requirements/mcp_calendar.txt requirements/mcp_calendar.txt
COPY requirements/mcp_gmail.txt requirements/mcp_gmail.txt
COPY src/frontend/gradio/requirements.txt requirements/gradio.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements/base.txt \
    && pip install --no-cache-dir -r requirements/db.txt \
    && pip install --no-cache-dir -r requirements/agent.txt \
    && pip install --no-cache-dir -r requirements/supervisor.txt \
    && pip install --no-cache-dir -r requirements/api.txt \
    && pip install --no-cache-dir -r requirements/cv_ui.txt \
    && pip install --no-cache-dir -r requirements/mcp_calendar.txt \
    && pip install --no-cache-dir -r requirements/mcp_gmail.txt \
    && pip install --no-cache-dir -r requirements/gradio.txt

# Copy application code
COPY src/ /app/src/
COPY secrets/ /app/secrets/

ENV PYTHONPATH=/app
EXPOSE 7860

# Create entry script inside the image (avoids missing file in build context)
RUN printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -e' \
  '' \
  '# Hugging Face provides PORT; default to 7860 locally' \
  'export PORT=\"${PORT:-7860}\"' \
  '' \
  '# Defaults for local in-container routing; can be overridden via env' \
  'export SUPERVISOR_API_URL=\"${SUPERVISOR_API_URL:-http://127.0.0.1:8080/api/v1/supervisor}\"' \
  'export DATABASE_API_URL=\"${DATABASE_API_URL:-http://127.0.0.1:8080/api/v1/db}\"' \
  'export CV_UPLOAD_API_URL=\"${CV_UPLOAD_API_URL:-http://127.0.0.1:8080/api/v1/cv}\"' \
  '' \
  '# Start FastAPI backend' \
  'uvicorn src.api.app:app --host 0.0.0.0 --port 8080 &' \
  '' \
  '# Give the API a moment to come up' \
  'sleep 2' \
  '' \
  '# Run Gradio frontend' \
  'python src/frontend/gradio/app.py' \
  > /app/start.sh \
  && chmod +x /app/start.sh

CMD ["/app/start.sh"]
