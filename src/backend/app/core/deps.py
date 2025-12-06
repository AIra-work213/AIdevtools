from typing import Generator, Optional
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.security import verify_token

logger = structlog.get_logger(__name__)

# Database setup
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> Generator[AsyncSession, None, None]:
    """Dependency for getting async DB session"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()


class RateLimiter:
    """Simple rate limiter using Redis"""

    def __init__(self):
        import redis.asyncio as redis
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def check_limit(self, key: str, limit: int = None, window: int = 60):
        """Check if rate limit is exceeded"""
        limit = limit or settings.RATE_LIMIT_PER_MINUTE

        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window)

            if current > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": str(window)},
                )
        except Exception as e:
            logger.error("Rate limiter error", error=str(e))
            # Fail open - don't block if Redis is down
            pass


# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme)
):
    """Get current user if token is provided, otherwise return None"""
    if not token:
        return None

    try:
        from app.core.security import verify_token
        token_data = verify_token(token, "access")
        # TODO: Load user from database
        return {"username": token_data.username}
    except:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> dict:
    """Get current authenticated user"""
    try:
        token_data = verify_token(token, "access")
        # TODO: Load user from database
        user = {"username": token_data.username, "id": 1}
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current active user"""
    # TODO: Check user active status
    return current_user


class CommonQueryParams:
    """Common query parameters for pagination and filtering"""

    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        sort: str = "created_at",
        order: str = "desc"
    ):
        self.skip = skip
        self.limit = limit
        self.sort = sort
        self.order = order