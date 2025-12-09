import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.test import (
    GenerationSettings,
    ManualTestRequest,
    TestMetadata,
    ChatMessage
)


def test_generation_settings_valid():
    """Test valid generation settings"""
    settings = GenerationSettings(
        test_type="manual",
        detail_level="detailed",
        use_aaa_pattern=True,
        include_negative_tests=True,
        temperature=0.7,
        max_tokens=8000,
        language="python",
        framework="pytest"
    )
    assert settings.test_type == "manual"
    assert settings.detail_level == "detailed"
    assert settings.temperature == 0.7


def test_generation_settings_defaults():
    """Test generation settings defaults"""
    settings = GenerationSettings()
    assert settings.test_type == "manual"
    assert settings.detail_level == "standard"
    assert settings.use_aaa_pattern is True
    assert settings.include_negative_tests is True
    assert settings.temperature is None  # Optional field
    assert settings.language == "python"
    assert settings.framework == "pytest"


def test_generation_settings_invalid_temperature():
    """Test invalid temperature values"""
    with pytest.raises(ValidationError):
        GenerationSettings(temperature=3.0)  # Too high

    with pytest.raises(ValidationError):
        GenerationSettings(temperature=-0.1)  # Too low


def test_generation_settings_invalid_max_tokens():
    """Test invalid max_tokens values"""
    with pytest.raises(ValidationError):
        GenerationSettings(max_tokens=50)  # Too low

    with pytest.raises(ValidationError):
        GenerationSettings(max_tokens=50000)  # Too high


def test_manual_test_request_with_all_fields():
    """Test manual test request with all fields"""
    now = datetime.now()
    request = ManualTestRequest(
        requirements="Create tests for login",
        metadata=TestMetadata(
            feature="Authentication",
            owner="QA Team",
            tags=["login", "auth"]
        ),
        generation_settings=GenerationSettings(
            detail_level="detailed",
            temperature=0.5
        ),
        conversation_history=[
            ChatMessage(
                type="user",
                content="Previous message",
                timestamp=now
            )
        ]
    )

    assert request.requirements == "Create tests for login"
    assert request.metadata.feature == "Authentication"
    assert request.generation_settings.detail_level == "detailed"
    assert len(request.conversation_history) == 1
    assert request.conversation_history[0].type == "user"


def test_manual_test_request_minimal():
    """Test manual test request with minimal fields"""
    request = ManualTestRequest(
        requirements="Create tests"
    )

    assert request.requirements == "Create tests"
    assert request.metadata is None
    assert request.generation_settings is None
    assert request.conversation_history is None


def test_chat_message_schema():
    """Test chat message schema"""
    now = datetime.now()
    message = ChatMessage(
        id="123",
        type="user",
        content="Hello",
        timestamp=now,
        metadata={
            "code": "print('hello')",
            "testCases": ["test1", "test2"]
        }
    )

    assert message.id == "123"
    assert message.type == "user"
    assert message.content == "Hello"
    assert message.timestamp == now
    assert message.metadata["code"] == "print('hello')"


def test_chat_message_optional_fields():
    """Test chat message without optional fields"""
    message = ChatMessage(
        type="assistant",
        content="Response"
    )

    assert message.type == "assistant"
    assert message.content == "Response"
    assert message.id is None
    assert message.timestamp is None
    assert message.metadata is None