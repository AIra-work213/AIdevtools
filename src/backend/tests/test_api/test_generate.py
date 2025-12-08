import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.schemas.test import ManualTestRequest, ApiTestRequest


@pytest.mark.asyncio
class TestGenerateAPI:
    """Test API endpoints for test generation"""

    async def test_generate_manual_success(self, client: AsyncClient):
        """Test successful manual test generation"""
        request_data = {
            "requirements": "User should be able to login with valid credentials",
            "metadata": {
                "feature": "Authentication",
                "story": "User Login",
                "owner": "QA Team"
            }
        }

        with patch('app.api.v1.endpoints.generate.AIService') as mock_service:
            # Mock the AI service response
            mock_instance = AsyncMock()
            mock_instance.generate_manual_tests.return_value = {
                "code": """
@allure.feature("Authentication")
@allure.story("User Login")
@allure.label("owner", "QA Team")
@allure.tag("generated_by_ai")
class TestGeneratedTests:
    @allure.title("User login with valid credentials")
    @allure.severity(allure.severity_level.HIGH)
    @allure.manual
    def test_user_login_valid_credentials(self):
        with allure.step("Open login page"):
            pass
        with allure.step("Enter valid credentials"):
            pass
        with allure.step("Verify login success"):
            pass
                """,
                "test_cases": [
                    {
                        "title": "User login with valid credentials",
                        "description": "Test login functionality",
                        "steps": ["Open page", "Enter credentials", "Verify"],
                        "expected_result": "Login successful",
                        "priority": "high",
                        "tags": ["auth"]
                    }
                ],
                "generation_time": 2.5
            }
            mock_instance.validate_code.return_value = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
            mock_service.return_value = mock_instance

            response = await client.post(
                "/api/v1/generate/manual",
                json=request_data
            )

        assert response.status_code == 200
        data = response.json()

        assert "code" in data
        assert "test_cases" in data
        assert "validation" in data
        assert "generation_time" in data

        # Verify code contains Allure decorators
        code = data["code"]
        assert "@allure.feature" in code
        assert "@allure.story" in code
        assert "def test_" in code

    async def test_generate_manual_invalid_input(self, client: AsyncClient):
        """Test manual test generation with invalid input"""
        request_data = {
            "requirements": "",  # Empty requirements
            "metadata": {}
        }

        response = await client.post(
            "/api/v1/generate/manual",
            json=request_data
        )

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("requirements" in str(error) for error in errors)

    async def test_generate_api_tests_success(self, client: AsyncClient, sample_openapi_spec):
        """Test successful API test generation"""
        request_data = {
            "openapi_spec": sample_openapi_spec,
            "endpoint_filter": ["/users"],
            "test_types": ["happy_path", "negative"]
        }

        with patch('app.api.v1.endpoints.generate.AIService') as mock_service:
            mock_instance = AsyncMock()
            mock_instance.generate_api_tests.return_value = {
                "code": """
import pytest
import requests

class TestUserAPI:
    def test_get_users_success(self):
        response = requests.get("/users")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
                """,
                "endpoints_covered": ["/users"],
                "test_matrix": {
                    "/users": ["get_success", "post_success", "post_invalid"]
                },
                "generation_time": 3.0
            }
            mock_instance.validate_code.return_value = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
            mock_service.return_value = mock_instance

            response = await client.post(
                "/api/v1/generate/auto/api",
                json=request_data
            )

        assert response.status_code == 200
        data = response.json()

        assert "code" in data
        assert "endpoints_covered" in data
        assert "test_matrix" in data
        assert "coverage_percentage" in data

        assert "/users" in data["endpoints_covered"]
        assert len(data["test_matrix"]) > 0

    async def test_generate_api_tests_invalid_spec(self, client: AsyncClient):
        """Test API test generation with invalid OpenAPI spec"""
        request_data = {
            "openapi_spec": "invalid yaml content",
            "test_types": ["happy_path"]
        }

        with patch('app.api.v1.endpoints.generate.AIService') as mock_service:
            mock_instance = AsyncMock()
            mock_instance.generate_api_tests.side_effect = ValueError("Invalid OpenAPI spec")
            mock_service.return_value = mock_instance

            response = await client.post(
                "/api/v1/generate/auto/api",
                json=request_data
            )

        assert response.status_code == 500
        assert "Failed to generate API tests" in response.json()["detail"]

    async def test_rate_limiting(self, client: AsyncClient):
        """Test rate limiting on generate endpoints"""
        request_data = {
            "requirements": "Simple test requirement"
        }

        # Make multiple requests quickly
        responses = []
        for _ in range(12):  # Exceed default rate limit of 10 per minute
            response = await client.post(
                "/api/v1/generate/manual",
                json=request_data
            )
            responses.append(response)

        # At least one should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Rate limiting should be enforced"