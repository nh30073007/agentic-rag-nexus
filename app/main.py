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
    # Startup: Create tables if not exist
    print("🚀 Creating database tables if not exist...")
    Base.metadata.create_all(bind=engine)
    
    print(f"🚀 {settings.APP_NAME} starting...")
    print(f"📡 Environment: {settings.ENVIRONMENT}")
    print(f"🤖 LLM Provider: {settings.DEFAULT_LLM_PROVIDER}")
    print(f"🗄️  Database: {settings.DATABASE_URL}")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent Document Intelligence with Human-in-the-Loop",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }