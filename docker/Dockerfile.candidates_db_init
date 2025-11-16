# Use a slim, modern Python base
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies needed for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Default command (overridden by docker-compose.yml)
CMD ["python", "-m", "src.database.candidates.client"]
