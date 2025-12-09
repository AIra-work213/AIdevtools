from fastapi import APIRouter

from app.api.v1.endpoints import (
    generate,
    analyze,
    gitlab,
    health,
    coverage
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    generate.router,
    prefix="/generate",
    tags=["generation"]
)

api_router.include_router(
    analyze.router,
    prefix="/analyze",
    tags=["analysis"]
)

api_router.include_router(
    gitlab.router,
    prefix="/gitlab",
    tags=["gitlab"]
)

api_router.include_router(
    coverage.router,
    prefix="/coverage",
    tags=["coverage"]
)

# TODO: Add auth router
# api_router.include_router(
#     auth.router,
#     prefix="/auth",
#     tags=["authentication"]
# )