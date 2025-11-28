"""
FastAPI Application for Recruitment Agent API.

Run with:
    uvicorn src.api.app:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import supervisor, cv_upload, voice_screener, database
from src.configs import get_openai_settings

# Validate OpenAI API key at startup (shows nice error if missing)
get_openai_settings()

app = FastAPI(
    title="Recruitment Agent API",
    description="API layer for the HR Supervisor Agent and recruitment tools",
    version="1.0.0",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(supervisor.router, prefix="/api/v1/supervisor", tags=["Supervisor"])
app.include_router(cv_upload.router, prefix="/api/v1/cv", tags=["CV Upload"])
app.include_router(database.router, prefix="/api/v1/db", tags=["Database"])
app.include_router(voice_screener.router, prefix="/api/v1/voice-screener", tags=["Voice Screener"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.
    """
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint with API info.
    """
    return {
        "message": "Recruitment Agent API",
        "docs": "/docs",
        "health": "/health",
    }

