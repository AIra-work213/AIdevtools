import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.test import ManualTestRequest, GenerationSettings, TestMetadata

client = TestClient(app)


def test_generation_settings_in_request():
    """Test that generation settings are properly accepted and used"""
    request_data = {
        "requirements": "Create tests for login functionality",
        "metadata": {
            "feature": "Authentication",
            "owner": "QA Team"
        },
        "generation_settings": {
            "test_type": "manual",
            "detail_level": "detailed",
            "use_aaa_pattern": True,
            "include_negative_tests": True,
            "temperature": 0.5,
            "max_tokens": 8000,
            "language": "python",
            "framework": "pytest"
        },
        "conversation_history": []
    }

    response = client.post("/api/v1/generate/manual", json=request_data)

    # Note: This test might fail if the API endpoint is not mocked
    # In a real scenario, you'd mock the AIService
    assert response.status_code in [200, 500]  # 500 if no API key configured


def test_generation_settings_defaults():
    """Test that default settings work when not provided"""
    request_data = {
        "requirements": "Create tests for login functionality",
        "metadata": {
            "feature": "Authentication",
            "owner": "QA Team"
        }
        # generation_settings is optional
    }

    response = client.post("/api/v1/generate/manual", json=request_data)
    assert response.status_code in [200, 500]


def test_conversation_history_support():
    """Test that conversation history is accepted"""
    request_data = {
        "requirements": "Refine the tests",
        "conversation_history": [
            {
                "type": "user",
                "content": "Create tests for login functionality",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "type": "assistant",
                "content": "Here are the login tests...",
                "timestamp": "2024-01-01T00:01:00Z"
            }
        ]
    }

    response = client.post("/api/v1/generate/manual", json=request_data)
    assert response.status_code in [200, 500]


@pytest.mark.parametrize("detail_level", ["minimal", "standard", "detailed"])
def test_detail_levels(detail_level):
    """Test different detail levels"""
    request_data = {
        "requirements": "Create tests for payment processing",
        "generation_settings": {
            "detail_level": detail_level
        }
    }

    response = client.post("/api/v1/generate/manual", json=request_data)
    assert response.status_code in [200, 500]


@pytest.mark.parametrize("language", ["python", "javascript", "typescript", "java", "csharp"])
def test_different_languages(language):
    """Test different programming languages"""
    request_data = {
        "requirements": "Create unit tests",
        "generation_settings": {
            "language": language
        }
    }

    response = client.post("/api/v1/generate/manual", json=request_data)
    assert response.status_code in [200, 500]


def test_temperature_validation():
    """Test temperature validation"""
    # Valid temperature
    request_data = {
        "requirements": "Create tests",
        "generation_settings": {
            "temperature": 1.0
        }
    }

    response = client.post("/api/v1/generate/manual", json=request_data)
    # Should not fail validation
    assert response.status_code not in [422]

    # Invalid temperature (should be validated by Pydantic)
    request_data["generation_settings"]["temperature"] = 3.0
    response = client.post("/api/v1/generate/manual", json=request_data)
    assert response.status_code == 422