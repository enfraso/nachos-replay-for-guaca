"""
Nachos Replay for Guaca - FastAPI Main Application
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import settings
from app.database import init_db
from app.api import api_router
from app.tasks.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.app_name} v{__version__}")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Start scheduler for background tasks
    start_scheduler()
    logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    stop_scheduler()
    logger.info("Scheduler stopped")
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Sistema de Replay e Auditoria de Sessões Apache Guacamole",
    version=__version__,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type", "Content-Disposition", "X-Total-Duration"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = datetime.now(timezone.utc)
    
    response = await call_next(request)
    
    process_time = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    logger.debug(
        f"{request.method} {request.url.path} "
        f"- {response.status_code} - {process_time:.3f}s"
    )
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )


# Include API router
app.include_router(api_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    from app.schemas import HealthCheck
    
    return HealthCheck(
        status="healthy",
        version=__version__,
        database="connected",
        timestamp=datetime.now(timezone.utc)
    )


# Root redirect
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": __version__,
        "docs": "/docs" if settings.debug else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
