## 🐳 Docker Services

### Services and Ports

| Service | Description | Host Port | Container Port |
|---------|-------------|-----------|----------------|
| `db` | PostgreSQL 15 database with persistent storage | 5433 | 5432 |
| `candidates_db_init` | Python backend container — initializes DB schema | N/A | N/A |
| `cv_upload_streamlit` | Streamlit app for CV uploads | 8501 | 8501 |
| `websocket_proxy` | WebSocket proxy for OpenAI Realtime API | 8000 | 8000 |
| `voice_screening_streamlit` | Streamlit app for voice screening | 8502 | 8501 |
| `supervisor_ui` | Streamlit app for Supervisor Agent | 8503 | 8501 |

---

### Run Command

```bash
docker compose --env-file .env -f docker/docker-compose.yml up --build
```

---

### Resetting the Environment

When making structural changes to the database (e.g., modifying models, updating Enums) or when you simply want a clean slate for testing, the persistent Docker volumes may cause conflicts with new code.

To completely reset the environment and database:

```bash
# 1. Stop running containers
docker compose -f docker/docker-compose.yml down

# 2. Remove the persistent database volume
docker volume rm docker_postgres_data

# 3. Rebuild and start fresh
docker compose --env-file .env -f docker/docker-compose.yml up --build
```
