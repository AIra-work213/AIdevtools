"""Tests for network error handling"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
import httpx
from app.services.ai_service import ai_service
from app.services.validation_service import validation_service
from app.api.v1.endpoints.generate import manual_test
from app.api.v1.endpoints.analyze import validate_code
from app.api.v1.endpoints.gitlab import create_mr


class TestAIServiceNetworkErrors:
    """Test AI service network error handling"""

    @pytest.mark.asyncio
    async def test_ai_service_timeout(self):
        """Test handling of AI service timeout"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Simulate timeout
            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(Exception) as exc_info:
                await ai_service.generate_code(
                    prompt="Generate test",
                    language="python"
                )
            assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_ai_service_connection_error(self):
        """Test handling of connection error to AI service"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Simulate connection error
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(Exception) as exc_info:
                await ai_service.generate_code(
                    prompt="Generate test",
                    language="python"
                )
            assert "connection" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_ai_service_rate_limit(self):
        """Test handling of rate limit errors"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Simulate rate limit response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                "error": "Rate limit exceeded"
            }
            mock_post.return_value = mock_response

            with pytest.raises(HTTPException) as exc_info:
                await ai_service.generate_code(
                    prompt="Generate test",
                    language="python"
                )
            assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_ai_service_server_error(self):
        """Test handling of 500 server errors"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Simulate server error
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.json.return_value = {
                "error": "Internal server error"
            }
            mock_post.return_value = mock_response

            with pytest.raises(HTTPException) as exc_info:
                await ai_service.generate_code(
                    prompt="Generate test",
                    language="python"
                )
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_ai_service_retry_on_failure(self):
        """Test retry mechanism for AI service calls"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # First call fails, second succeeds
            mock_response_fail = Mock()
            mock_response_fail.status_code = 503
            mock_response_fail.json.return_value = {"error": "Service unavailable"}

            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"code": "generated code"}

            mock_post.side_effect = [
                mock_response_fail,
                mock_response_success
            ]

            result = await ai_service.generate_code(
                prompt="Generate test",
                language="python",
                max_retries=2
            )
            assert result == "generated code"
            assert mock_post.call_count == 2


class TestGitLabServiceNetworkErrors:
    """Test GitLab service network error handling"""

    @pytest.mark.asyncio
    async def test_gitlab_api_error(self):
        """Test GitLab API error handling"""
        with patch('app.services.gitlab_service.gitlab_client') as mock_client:
            # Simulate GitLab API error
            mock_client.projects.get.side_effect = Exception("GitLab API error")

            with pytest.raises(HTTPException) as exc_info:
                from app.api.v1.endpoints.gitlab import get_project
                await get_project(123)
            assert "gitlab" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_gitlab_authentication_error(self):
        """Test GitLab authentication error"""
        with patch('app.services.gitlab_service.gitlab_client') as mock_client:
            # Simulate auth error
            mock_client.auth.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                from app.api.v1.endpoints.gitlab import get_projects
                await get_projects()
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_gitlab_timeout(self):
        """Test GitLab timeout handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Simulate timeout
            mock_get.side_effect = httpx.TimeoutException("GitLab API timeout")

            with pytest.raises(HTTPException) as exc_info:
                from app.api.v1.endpoints.gitlab import get_branches
                await get_branches(123)
            assert "timeout" in exc_info.value.detail.lower()


class TestValidationServiceNetworkErrors:
    """Test validation service network error handling"""

    @pytest.mark.asyncio
    async def test_external_validation_service_error(self):
        """Test external validation service errors"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Simulate external service error
            mock_post.side_effect = httpx.ConnectError("Validation service unavailable")

            # Should gracefully fall back to local validation
            result = await validation_service.validate_code(
                code="def test(): pass",
                standards=["pytest"]
            )
            assert isinstance(result, dict)
            assert "is_valid" in result


class TestCoverageServiceNetworkErrors:
    """Test coverage service network error handling"""

    @pytest.mark.asyncio
    async def test_github_api_error(self):
        """Test GitHub API error during repository clone"""
        with patch('git.Repo.clone_from') as mock_clone:
            # Simulate Git error
            mock_clone.side_effect = Exception("Repository not found")

            from app.services.coverage_service import CodeUploader
            with pytest.raises(Exception) as exc_info:
                await CodeUploader.upload_from_github("https://github.com/invalid/repo.git")
            assert "repository" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_github_rate_limit(self):
        """Test GitHub rate limit handling"""
        with patch('urllib.request.urlopen') as mock_urlopen:
            # Simulate rate limit response
            mock_response = Mock()
            mock_response.code = 403
            mock_response.headers = {"X-RateLimit-Remaining": "0"}
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with pytest.raises(HTTPException) as exc_info:
                from app.api.v1.endpoints.coverage import upload_from_github
                await upload_from_github("https://github.com/user/repo.git")
            assert "rate limit" in exc_info.value.detail.lower()


class TestEndpointErrorHandling:
    """Test API endpoint error handling"""

    @pytest.mark.asyncio
    async def test_generate_endpoint_malformed_request(self):
        """Test generate endpoint with malformed request"""
        # Missing required fields
        with pytest.raises(HTTPException) as exc_info:
            await manual_test(
                ManualTestRequest(
                    requirements="x"  # Too short
                )
            )
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_endpoint_empty_code(self):
        """Test analyze endpoint with empty code"""
        with pytest.raises(HTTPException) as exc_info:
            await validate_code(
                ValidationRequest(
                    code="",
                    standards=["pytest"]
                )
            )
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_coverage_endpoint_invalid_url(self):
        """Test coverage endpoint with invalid repository URL"""
        from app.api.v1.endpoints.coverage import upload_from_github

        with pytest.raises(HTTPException) as exc_info:
            await upload_from_github("invalid-url")
        assert exc_info.value.status_code == 400


class TestNetworkRetryLogic:
    """Test network retry logic"""

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff in retry logic"""
        call_times = []

        async def mock_request(*args, **kwargs):
            import time
            call_times.append(time.time())
            if len(call_times) < 3:
                raise httpx.ConnectError("Connection failed")
            return Mock(status_code=200, json=lambda: {"result": "success"})

        with patch('httpx.AsyncClient.post', side_effect=mock_request):
            import asyncio
            from app.utils.http_client import make_request_with_retry

            result = await make_request_with_retry(
                url="http://example.com/api",
                max_retries=3,
                backoff_factor=0.1
            )
            assert result["result"] == "success"
            assert len(call_times) == 3

            # Verify exponential backoff
            assert call_times[1] - call_times[0] >= 0.1
            assert call_times[2] - call_times[1] >= 0.2

    @pytest.mark.asyncio
    async def test_max_retry_limit(self):
        """Test maximum retry limit enforcement"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Always fail
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(Exception):
                from app.utils.http_client import make_request_with_retry
                await make_request_with_retry(
                    url="http://example.com/api",
                    max_retries=3
                )

            # Should only retry 3 times + 1 initial attempt
            assert mock_post.call_count == 4


class TestCircuitBreaker:
    """Test circuit breaker pattern for network calls"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_open(self):
        """Test circuit breaker opens after failure threshold"""
        from app.utils.circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1
        )

        # Simulate failures
        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.call(lambda: exec("raise Exception('Service error')"))

        # Circuit should be open
        assert breaker.is_open()

        # Next call should fail fast
        with pytest.raises(Exception) as exc_info:
            await breaker.call(lambda: "success")
        assert "circuit breaker" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout"""
        from app.utils.circuit_breaker import CircuitBreaker
        import asyncio

        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1  # Short timeout for testing
        )

        # Trigger circuit breaker
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(lambda: exec("raise Exception('Service error')"))

        assert breaker.is_open()

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # Next call should succeed
        result = await breaker.call(lambda: "recovered")
        assert result == "recovered"
        assert not breaker.is_open()


@pytest.fixture
async def mock_http_client():
    """Mock HTTP client for testing"""
    with patch('httpx.AsyncClient') as mock_client:
        yield mock_client


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing"""
    with patch('app.services.ai_service.ai_service') as mock_service:
        mock_service.generate_code = AsyncMock(return_value="generated code")
        yield mock_service