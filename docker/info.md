## 🐳 Docker Services

### Run Command

```bash
docker compose --env-file .env -f docker/docker-compose.yml up --build
```

### Services and Ports

| Service | Description | Host Port | Container Port |
|---------|-------------|-----------|----------------|
| `db` | PostgreSQL 15 database with persistent storage | 5433 | 5432 |
| `candidates_db_init` | Python backend container — initializes DB schema | N/A | N/A |
| `cv_upload_streamlit` | Streamlit app for CV uploads | 8501 | 8501 |
| `websocket_proxy` | WebSocket proxy for OpenAI Realtime API | 8000 | 8000 |
| `voice_screening_streamlit` | Streamlit app for voice screening | 8502 | 8501 |
| `supervisor_ui` | Streamlit app for Supervisor Agent | 8503 | 8501 |
