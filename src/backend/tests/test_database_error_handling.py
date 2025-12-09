"""Tests for database error handling"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    DatabaseError,
    TimeoutError,
    DisconnectionError
)
from fastapi import HTTPException
import asyncpg
from app.core.database import get_db
# from app.models import *  # Models may not exist yet
# from app.services.history_service import history_service
# from app.api.v1.endpoints.history import get_chat_history, save_chat_history


class TestDatabaseConnectionErrors:
    """Test database connection error handling"""

    @pytest.mark.asyncio
    async def test_database_connection_timeout(self):
        """Test handling of database connection timeout"""
        with patch('asyncpg.connect') as mock_connect:
            # Simulate connection timeout
            mock_connect.side_effect = asyncpg.exceptions.ConnectionDoesNotExistError(
                "Connection timeout"
            )

            with pytest.raises(HTTPException) as exc_info:
                async for db in get_db():
                    await db.execute("SELECT 1")
                    break
            assert exc_info.value.status_code == 503
            assert "database" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_database_connection_refused(self):
        """Test handling of connection refused"""
        with patch('asyncpg.connect') as mock_connect:
            # Simulate connection refused
            mock_connect.side_effect = ConnectionRefusedError(
                "Database connection refused"
            )

            with pytest.raises(HTTPException) as exc_info:
                from app.core.database import check_database_health
                await check_database_health()
            assert "unavailable" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_database_credentials_error(self):
        """Test handling of invalid database credentials"""
        with patch('asyncpg.connect') as mock_connect:
            # Simulate authentication error
            mock_connect.side_effect = asyncpg.exceptions.InvalidPasswordError(
                "Invalid password"
            )

            with pytest.raises(HTTPException) as exc_info:
                async for db in get_db():
                    await db.execute("SELECT 1")
                    break
            assert exc_info.value.status_code == 500
            assert "authentication" in exc_info.value.detail.lower()


class TestDatabaseOperationalErrors:
    """Test database operational error handling"""

    @pytest.mark.asyncio
    async def test_database_lock_timeout(self):
        """Test handling of database lock timeout"""
        with patch('asyncpg.Connection.execute') as mock_execute:
            # Simulate lock timeout
            mock_execute.side_effect = asyncpg.exceptions.QueryCanceledError(
                "Query canceled due to lock timeout"
            )

            with pytest.raises(HTTPException) as exc_info:
                await history_service.save_chat(
                    user_id="user123",
                    message="test message",
                    message_type="user"
                )
            assert exc_info.value.status_code == 408
            assert "timeout" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_database_constraint_violation(self):
        """Test handling of constraint violations"""
        with patch('asyncpg.Connection.execute') as mock_execute:
            # Simulate unique constraint violation
            mock_execute.side_effect = asyncpg.exceptions.UniqueViolationError(
                "duplicate key value violates unique constraint"
            )

            with pytest.raises(HTTPException) as exc_info:
                await history_service.save_chat(
                    user_id="user123",
                    message="test message",
                    message_type="user"
                )
            assert exc_info.value.status_code == 409
            assert "duplicate" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_foreign_key_violation(self):
        """Test handling of foreign key violations"""
        with patch('asyncpg.Connection.execute') as mock_execute:
            # Simulate foreign key violation
            mock_execute.side_effect = asyncpg.exceptions.ForeignKeyViolationError(
                "violates foreign key constraint"
            )

            with pytest.raises(HTTPException) as exc_info:
                await history_service.save_chat(
                    user_id="nonexistent_user",
                    message="test message",
                    message_type="user"
                )
            assert exc_info.value.status_code == 400
            assert "reference" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_check_violation(self):
        """Test handling of check constraint violations"""
        with patch('asyncpg.Connection.execute') as mock_execute:
            # Simulate check constraint violation
            mock_execute.side_effect = asyncpg.exceptions.CheckViolationError(
                "violates check constraint"
            )

            with pytest.raises(HTTPException) as exc_info:
                await history_service.save_chat(
                    user_id="user123",
                    message="",  # Empty message might violate constraint
                    message_type="user"
                )
            assert exc_info.value.status_code == 400
            assert "constraint" in exc_info.value.detail.lower()


class TestDatabaseQueryErrors:
    """Test database query error handling"""

    @pytest.mark.asyncio
    async def test_invalid_sql_syntax(self):
        """Test handling of invalid SQL syntax"""
        with patch('asyncpg.Connection.fetch') as mock_fetch:
            # Simulate SQL syntax error
            mock_fetch.side_effect = asyncpg.exceptions.SyntaxError(
                "syntax error at or near"
            )

            with pytest.raises(HTTPException) as exc_info:
                await get_chat_history(
                    user_id="user123",
                    limit=10,
                    offset=0
                )
            assert exc_info.value.status_code == 500
            assert "query" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_query_parameter_error(self):
        """Test handling of query parameter errors"""
        with patch('asyncpg.Connection.fetch') as mock_fetch:
            # Simulate parameter error
            mock_fetch.side_effect = asyncpg.exceptions.ProgramLimitExceeded(
                "too many SQL variables"
            )

            with pytest.raises(HTTPException) as exc_info:
                await get_chat_history(
                    user_id="user123",
                    limit=10000,  # Too large
                    offset=0
                )
            assert exc_info.value.status_code == 400
            assert "limit" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_insufficient_privileges(self):
        """Test handling of insufficient database privileges"""
        with patch('asyncpg.Connection.fetch') as mock_fetch:
            # Simulate privilege error
            mock_fetch.side_effect = asyncpg.exceptions.InsufficientPrivilegeError(
                "permission denied for relation"
            )

            with pytest.raises(HTTPException) as exc_info:
                await get_chat_history(
                    user_id="user123",
                    limit=10,
                    offset=0
                )
            assert exc_info.value.status_code == 403
            assert "permission" in exc_info.value.detail.lower()


class TestTransactionErrors:
    """Test database transaction error handling"""

    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """Test transaction rollback on error"""
        with patch('asyncpg.Connection.transaction') as mock_transaction:
            # Simulate transaction error
            mock_transaction.side_effect = asyncpg.exceptions.TransactionRollbackError(
                "transaction rolled back"
            )

            with pytest.raises(HTTPException) as exc_info:
                await save_chat_history(
                    user_id="user123",
                    messages=[
                        {"type": "user", "content": "message 1"},
                        {"type": "assistant", "content": "message 2"}
                    ]
                )
            assert "transaction" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_deadlock_detection(self):
        """Test handling of database deadlocks"""
        with patch('asyncpg.Connection.execute') as mock_execute:
            # Simulate deadlock
            mock_execute.side_effect = asyncpg.exceptions.DeadlockDetected(
                "deadlock detected"
            )

            with pytest.raises(HTTPException) as exc_info:
                await history_service.save_chat(
                    user_id="user123",
                    message="test message",
                    message_type="user"
                )
            assert exc_info.value.status_code == 409
            assert "deadlock" in exc_info.value.detail.lower()


class TestDatabasePoolErrors:
    """Test database connection pool errors"""

    @pytest.mark.asyncio
    async def test_pool_exhaustion(self):
        """Test handling of connection pool exhaustion"""
        with patch('asyncpg.create_pool') as mock_pool:
            # Simulate pool exhaustion
            mock_pool.side_effect = asyncpg.exceptions.TooManyConnectionsError(
                "too many connections"
            )

            with pytest.raises(HTTPException) as exc_info:
                from app.core.database import get_db_pool
                await get_db_pool()
            assert exc_info.value.status_code == 503
            assert "pool" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_pool_closed_error(self):
        """Test handling of operations on closed pool"""
        with patch('asyncpg.Pool.acquire') as mock_acquire:
            # Simulate closed pool
            mock_acquire.side_effect = asyncpg.exceptions.InterfaceError(
                "pool is closed"
            )

            with pytest.raises(HTTPException) as exc_info:
                async for db in get_db():
                    await db.execute("SELECT 1")
                    break
            assert exc_info.value.status_code == 503
            assert "unavailable" in exc_info.value.detail.lower()


class TestDatabaseMigrationErrors:
    """Test database migration error handling"""

    @pytest.mark.asyncio
    async def test_migration_lock_error(self):
        """Test handling of migration lock errors"""
        with patch('alembic.command.upgrade') as mock_upgrade:
            # Simulate migration lock
            mock_upgrade.side_effect = Exception("Migration is already in progress")

            with pytest.raises(HTTPException) as exc_info:
                from app.core.database import run_migrations
                await run_migrations()
            assert "migration" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_migration_dependency_error(self):
        """Test handling of migration dependency errors"""
        with patch('alembic.command.upgrade') as mock_upgrade:
            # Simulate dependency error
            mock_upgrade.side_effect = Exception("Migration dependency not found")

            with pytest.raises(HTTPException) as exc_info:
                from app.core.database import run_migrations
                await run_migrations()
            assert exc_info.value.status_code == 500


class TestDatabaseRetryLogic:
    """Test database operation retry logic"""

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Test retry on transient database errors"""
        attempts = []

        async def mock_execute(query, *args):
            attempts.append(1)
            if len(attempts) <= 2:
                raise asyncpg.exceptions.ConnectionDoesNotExistError(
                    "Connection lost"
                )
            return Mock()

        with patch('asyncpg.Connection.execute', side_effect=mock_execute):
            # Should succeed after retries
            result = await history_service.save_chat(
                user_id="user123",
                message="test message",
                message_type="user",
                max_retries=3
            )
            assert len(attempts) == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self):
        """Test no retry on permanent database errors"""
        attempts = []

        async def mock_execute(query, *args):
            attempts.append(1)
            raise asyncpg.exceptions.UniqueViolationError(
                "duplicate key"
            )

        with patch('asyncpg.Connection.execute', side_effect=mock_execute):
            # Should not retry on unique violation
            with pytest.raises(HTTPException):
                await history_service.save_chat(
                    user_id="user123",
                    message="test message",
                    message_type="user",
                    max_retries=3
                )
            assert len(attempts) == 1


class TestDatabaseHealthCheck:
    """Test database health check error handling"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        with patch('asyncpg.Connection.fetchval') as mock_fetch:
            mock_fetch.return_value = 1

            result = await check_database_health()
            assert result["status"] == "healthy"
            assert result["database"] == "ok"

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure"""
        with patch('asyncpg.Connection.fetchval') as mock_fetch:
            mock_fetch.side_effect = asyncpg.exceptions.ConnectionDoesNotExistError(
                "Connection failed"
            )

            result = await check_database_health()
            assert result["status"] == "unhealthy"
            assert "error" in result["database"]


@pytest.fixture
async def mock_db_session():
    """Mock database session for testing"""
    with patch('asyncpg.Connection') as mock_conn:
        mock_conn.execute = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_conn.transaction = AsyncMock()
        yield mock_conn


@pytest.fixture
async def sample_chat_data():
    """Sample chat data for testing"""
    return {
        "user_id": "test_user_123",
        "session_id": "session_456",
        "messages": [
            {"type": "user", "content": "Hello"},
            {"type": "assistant", "content": "Hi there!"}
        ],
        "metadata": {"source": "web", "version": "1.0"}
    }