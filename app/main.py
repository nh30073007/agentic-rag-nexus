"""
Agentic RAG Nexus - FastAPI Application Entry Point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""

    print("🚀 Creating database tables if not exist...")

    Base.metadata.create_all(bind=engine)

    print(f"🚀 {settings.APP_NAME} starting...")
    print(f"📡 Environment: {settings.ENVIRONMENT}")
    print(f"🤖 LLM Provider: {settings.DEFAULT_LLM_PROVIDER}")
    print(f"🗄️  Database: {settings.DATABASE_URL}")

    yield

    print("👋 Shutting down...")


# =========================================================
# CORS
# =========================================================

ALLOWED_ORIGINS = [
    "https://agentic-rag-nexus.streamlit.app",
    "http://localhost:8501",
    "http://localhost:8000",
    "http://localhost:3000",
]


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent Document Intelligence with Human-in-the-Loop",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# =========================================================
# CORS MIDDLEWARE
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# =========================================================
# API ROUTES
# =========================================================

app.include_router(
    api_router,
    prefix="/api/v1",
)


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
async def root():
    """Root endpoint."""

    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }