from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog
import json

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Docker deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "test", "*.cloud.ru"]
)


# Middleware for logging request bodies
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Cache request body for logging
    body_bytes = await request.body()
    
    # Log request details
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body_str = body_bytes.decode('utf-8')
            logger.info(
                "Incoming request",
                method=request.method,
                url=str(request.url),
                headers={k: v for k, v in request.headers.items() if k.lower() not in ['authorization', 'cookie']},
                body_preview=body_str[:500] if len(body_str) > 500 else body_str
            )
        except Exception as e:
            logger.error("Error reading request body", error=str(e))
    
    # Create a new request with cached body
    async def receive():
        return {"type": "http.request", "body": body_bytes}
    
    request._receive = receive
    
    # Process request
    response = await call_next(request)
    
    # Log response status for non-2xx responses
    if response.status_code >= 400:
        logger.warning(
            "Request failed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code
        )
    
    return response


# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(
        "Validation error",
        method=request.method,
        url=str(request.url),
        errors=exc.errors(),
        body=await request.body()
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
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