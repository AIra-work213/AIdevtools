import pytest
from unittest.mock import AsyncMock, patch
from app.services.ai_service import AIService


@pytest.fixture
def ai_service():
    return AIService()


@pytest.mark.asyncio
async def test_generate_manual_tests_with_settings(ai_service):
    """Test that AI service uses generation settings"""
    requirements = "Create tests for user registration"
    metadata = {"feature": "Authentication", "owner": "QA Team"}
    generation_settings = {
        "detail_level": "detailed",
        "use_aaa_pattern": True,
        "include_negative_tests": True,
        "temperature": 0.7,
        "max_tokens": 8000,
        "language": "python",
        "framework": "pytest"
    }

    # Mock the LLM client
    with patch.object(ai_service.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = """
import allure
import pytest
from allure_commons.types import Severity

@allure.feature("Authentication")
@allure.story("User Registration")
@allure.label("owner", "QA Team")
@allure.tag("generated_by_ai")
class TestUserRegistration:

    @allure.title("Test successful user registration")
    @allure.severity(Severity.HIGH)
    @allure.manual
    def test_successful_registration(self):
        \"\"\"Test user registration with valid data\"\"\"
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }

        with allure.step("Step 1: Navigate to registration page"):
            # TODO: Navigate to registration
            pass

        # Act
        with allure.step("Step 2: Fill registration form"):
            # TODO: Fill form
            pass

        with allure.step("Assert: User is registered"):
            # TODO: Verify registration
            pass
"""

        result = await ai_service.generate_manual_tests(
            requirements=requirements,
            metadata=metadata,
            generation_settings=generation_settings
        )

        # Verify the LLM was called with correct parameters
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args

        # Check temperature and max_tokens from settings
        assert call_args.kwargs['temperature'] == 0.7
        assert call_args.kwargs['max_tokens'] == 8000

        # Check that the prompt contains settings-specific instructions
        messages = call_args.kwargs['messages']
        user_prompt = messages[1]['content']

        assert "detailed" in user_prompt.lower()
        assert "Arrange-Act-Assert" in user_prompt
        assert "negative test" in user_prompt.lower()
        assert "python" in user_prompt.lower()
        assert "pytest" in user_prompt.lower()

        # Verify result structure
        assert 'code' in result
        assert 'test_cases' in result
        assert 'generation_time' in result
        assert result['metadata'] == metadata


@pytest.mark.asyncio
async def test_generate_with_conversation_history(ai_service):
    """Test that AI service uses conversation history for context"""
    requirements = "Add more test cases"
    conversation_history = [
        {
            'type': 'user',
            'content': 'Create tests for login functionality',
            'timestamp': '2024-01-01T00:00:00Z'
        },
        {
            'type': 'assistant',
            'content': 'I created login tests with positive scenarios',
            'timestamp': '2024-01-01T00:01:00Z'
        }
    ]

    with patch.object(ai_service.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = "# Additional test code"

        await ai_service.generate_manual_tests(
            requirements=requirements,
            conversation_history=conversation_history
        )

        # Verify history was included in the prompt
        call_args = mock_completion.call_args
        messages = call_args.kwargs['messages']
        user_prompt = messages[1]['content']

        assert "Previous conversation context:" in user_prompt
        assert "login functionality" in user_prompt
        assert "positive scenarios" in user_prompt


@pytest.mark.asyncio
async def test_generate_with_minimal_settings(ai_service):
    """Test generation with minimal detail level"""
    requirements = "Create basic tests"

    with patch.object(ai_service.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = "# Minimal test code"

        await ai_service.generate_manual_tests(
            requirements=requirements,
            generation_settings={
                "detail_level": "minimal",
                "include_negative_tests": False
            }
        )

        call_args = mock_completion.call_args
        user_prompt = call_args.kwargs['messages'][1]['content']

        assert "minimal tests with only essential" in user_prompt
        assert "Error conditions" not in user_prompt  # Should not include negative tests


@pytest.mark.asyncio
async def test_generate_different_language(ai_service):
    """Test generation with different programming language"""
    requirements = "Create tests"

    with patch.object(ai_service.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = "// JavaScript test code"

        await ai_service.generate_manual_tests(
            requirements=requirements,
            generation_settings={
                "language": "javascript",
                "framework": "jest"
            }
        )

        call_args = mock_completion.call_args
        user_prompt = call_args.kwargs['messages'][1]['content']

        assert "javascript" in user_prompt.lower()
        assert "jest" in user_prompt.lower()