import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.main import app
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create async engine for tests
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_cloud_api_key():
    """Mock Cloud.ru API key for testing."""
    return "test_api_key_12345"


@pytest.fixture
def mock_gitlab_token():
    """Mock GitLab token for testing."""
    return "test_gitlab_token_12345"


@pytest.fixture
def sample_test_case():
    """Sample test case data for testing."""
    return {
        "id": 1,
        "title": "Test user login functionality",
        "description": "Verify user can login with valid credentials",
        "steps": [
            "Open login page",
            "Enter valid username and password",
            "Click login button",
            "Verify user is redirected to dashboard"
        ],
        "expected_result": "User successfully logged in",
        "priority": "high",
        "tags": ["authentication", "smoke"]
    }


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI specification for testing."""
    return """
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List all users
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                    name:
                      type: string
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
                  format: email
              required:
                - name
                - email
      responses:
        '201':
          description: User created successfully
        '400':
          description: Invalid input
  /users/{id}:
    get:
      summary: Get user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Successful response
        '404':
          description: User not found
"""