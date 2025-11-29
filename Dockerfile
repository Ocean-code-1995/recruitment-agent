FROM python:3.12-slim

WORKDIR /app

# System dependencies (include Postgres server so DB can run in-container)
RUN apt-get update && apt-get install -y gcc libpq-dev postgresql postgresql-contrib gosu && rm -rf /var/lib/apt/lists/*

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

# Copy entry script (includes Postgres startup)
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
