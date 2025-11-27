"""
FastAPI Application for Recruitment Agent API.

Run with:
    uvicorn src.api.app:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import supervisor, cv_upload

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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "Recruitment Agent API",
        "docs": "/docs",
        "health": "/health",
    }

