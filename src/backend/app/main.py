from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import setup_auth


# Setup logging
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting TestOps Copilot API", version=settings.VERSION)

    # Initialize database connections
    # Initialize vector store
    # Initialize AI clients

    yield

    # Shutdown
    logger.info("Shutting down TestOps Copilot API")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Add CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.cloud.ru"]
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe - check dependencies"""
    # TODO: Add actual dependency checks
    # - Database connection
    # - AI service availability
    # - Vector store connection
    # - GitLab API connectivity

    dependencies = {
        "database": "ok",  # TODO: Implement check
        "ai_service": "ok",  # TODO: Implement check
        "vector_store": "ok",  # TODO: Implement check
        "gitlab": "ok"  # TODO: Implement check
    }

    all_ok = all(status == "ok" for status in dependencies.values())

    return {
        "ready": all_ok,
        "dependencies": dependencies
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level=settings.LOG_LEVEL.lower(),
        log_config=None  # Using structlog instead
    )