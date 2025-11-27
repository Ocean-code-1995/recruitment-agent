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

### Database `/api/v1/db`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/query` | Flexible query any table |
| GET | `/candidates` | List candidates with filters |
| GET | `/candidates/{id}` | Get full candidate profile by UUID |
| GET | `/candidates/email/{email}` | Get full candidate profile by email |
| GET | `/cv-screening` | List CV screening results |
| GET | `/voice-screening` | List voice screening results |
| GET | `/interviews` | List interview scheduling |
| GET | `/decisions` | List final decisions |
| GET | `/stats` | Database statistics |
| GET | `/health` | Health check |

**Full Candidate Profile** (`/candidates/{id}` and `/candidates/email/{email}`):

Returns ALL data for a candidate including related records (by default `include_relations=true`):
- **Base fields:** id, full_name, email, phone_number, cv_file_path, parsed_cv_file_path, status, created_at, updated_at
- **cv_screening_results:** list of CV screening scores and feedback
- **voice_screening_results:** list of voice screening transcripts and scores
- **interview_scheduling:** list of scheduled interviews
- **final_decision:** hiring decision with rationale (if any)

Use `?include_relations=false` to fetch only base candidate fields.

**Flexible Query Example:**
```json
POST /api/v1/db/query
{
    "table": "candidates",
    "filters": {"status": "applied"},
    "fields": ["id", "full_name", "email"],
    "include_relations": true,
    "limit": 10,
    "offset": 0,
    "sort_by": "created_at",
    "sort_order": "desc"
}
```

**Supported filter operators:**
- `$eq`, `$ne`: equality/inequality
- `$gt`, `$gte`, `$lt`, `$lte`: comparisons
- `$in`, `$nin`: list membership
- `$like`, `$ilike`: pattern matching

## Structure

```
src/api/
├── app.py              ← FastAPI app + CORS + router mounting
├── routers/
│   ├── supervisor.py   ← Chat endpoints (regular + streaming)
│   ├── cv_upload.py    ← CV submission endpoint
│   └── database.py     ← Flexible database query endpoints
└── schemas/
    ├── supervisor_chat.py  ← ChatRequest, ChatResponse
    ├── cv_upload.py        ← SubmitResponse
    └── database.py         ← QueryRequest, QueryResponse, etc.
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

# Database Queries
from src.sdk import DatabaseClient
db = DatabaseClient()

# List candidates
candidates = db.get_candidates(status="applied", include_relations=True)
for c in candidates.data:
    print(c["full_name"], c["status"])

# Get full candidate profile by email
profile = db.get_candidate_by_email("ada@example.com")
print(profile.data["cv_screening_results"])

# Flexible query with filters
results = db.query(
    table="cv_screening_results",
    filters={"overall_fit_score": {"$gte": 0.8}},
    sort_by="overall_fit_score",
    sort_order="desc"
)

# Get database stats
stats = db.get_stats()
print(stats.stats["candidates"]["by_status"])
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
- [x] Candidate database router

