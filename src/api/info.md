# API Layer 🔌

> FastAPI backend decoupling agents from frontends.

## Quick Start

```bash
# Local
uvicorn src.api.app:app --reload --port 8080

# Docker
docker compose --env-file .env -f docker/docker-compose.yml up supervisor_api
```

**Docs:** http://localhost:8080/docs

## Endpoints

### Supervisor Agent `/api/v1/supervisor`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send message, get response |
| POST | `/chat/stream` | SSE streaming response |
| POST | `/new` | Create new chat session |
| GET | `/health` | Health check |

**Streaming (SSE) events:**
```
event: token    → {"content": "Hello"}
event: done     → {"thread_id": "abc123", "token_count": 150}
event: error    → {"error": "Something went wrong"}
```

### CV Upload `/api/v1/cv`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/submit` | Submit application + CV |
| GET | `/health` | Health check |

**Submit flow:**
1. Save CV file to disk
2. Register candidate in DB
3. Parse CV → Markdown (GPT-4 Vision)
4. Update parsed path in DB

## Structure

```
src/api/
├── app.py              ← FastAPI app + CORS + router mounting
├── routers/
│   ├── supervisor.py   ← Chat endpoints (regular + streaming)
│   └── cv_upload.py    ← CV submission endpoint
└── schemas/
    ├── supervisor_chat.py  ← ChatRequest, ChatResponse
    └── cv_upload.py        ← SubmitResponse
```

## SDK Clients

Frontends use SDK clients instead of raw HTTP:

```python
# Supervisor
from src.sdk import SupervisorClient
client = SupervisorClient()
for chunk in client.stream("Show candidates", thread_id):
    print(chunk.content)

# CV Upload
from src.sdk import CVUploadClient
client = CVUploadClient()
response = client.submit(name, email, phone, cv_file, filename)
```

## Environment

| Variable | Default | Used By |
|----------|---------|---------|
| `OPENAI_API_KEY` | required | Validated at startup |
| `CV_UPLOAD_PATH` | `src/database/cvs/uploads` | CV router |
| `CV_PARSED_PATH` | `src/database/cvs/parsed` | CV router |
| `POSTGRES_*` | varies | Database connection |

## TODO

- [ ] Voice agent router
- [ ] Candidate database router

