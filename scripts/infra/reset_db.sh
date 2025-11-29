#!/bin/bash
# Reset the database environment

echo "🛑 Stopping containers..."
docker compose -f docker/docker-compose.yml down

echo "🗑️ Removing database volume..."
docker volume rm docker_postgres_data

echo "🚀 Rebuilding and starting..."
docker compose --env-file .env -f docker/docker-compose.yml up --build

