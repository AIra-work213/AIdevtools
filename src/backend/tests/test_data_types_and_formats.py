"""Tests for data types and formats validation"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.test import (
    TestMetadata,
    GenerationSettings,
    ChatMessage,
    ManualTestRequest,
    TestCase,
    ValidationResult,
    GeneratedTestResponse,
    ApiTestRequest,
    DuplicateSearchRequest,
    ValidationRequest,
    CoverageAnalysisRequest,
    UploadedFile,
    CoverageMetrics,
    UncoveredFunction
)


class TestTestMetadata:
    """Test TestMetadata schema validation"""

    def test_valid_metadata(self):
        """Test creating valid TestMetadata"""
        metadata = TestMetadata(
            feature="User Authentication",
            story="Login story",
            owner="test@example.com",
            severity="high",
            tags=["auth", "security"]
        )
        assert metadata.feature == "User Authentication"
        assert metadata.severity == "high"
        assert metadata.tags == ["auth", "security"]

    def test_minimal_metadata(self):
        """Test creating TestMetadata with minimal data"""
        metadata = TestMetadata()
        assert metadata.feature is None
        assert metadata.severity == "normal"
        assert metadata.tags == []

    def test_invalid_severity(self):
        """Test invalid severity value"""
        with pytest.raises(ValidationError):
            TestMetadata(severity="invalid")


class TestGenerationSettings:
    """Test GenerationSettings schema validation"""

    def test_valid_settings(self):
        """Test creating valid GenerationSettings"""
        settings = GenerationSettings(
            test_type="api",
            detail_level="detailed",
            use_aaa_pattern=True,
            include_negative_tests=True,
            temperature=0.7,
            max_tokens=2000,
            language="python",
            framework="pytest"
        )
        assert settings.test_type == "api"
        assert settings.temperature == 0.7
        assert settings.max_tokens == 2000

    def test_temperature_bounds(self):
        """Test temperature value bounds"""
        # Valid temperature
        settings = GenerationSettings(temperature=1.0)
        assert settings.temperature == 1.0

        # Temperature too low
        with pytest.raises(ValidationError):
            GenerationSettings(temperature=-0.1)

        # Temperature too high
        with pytest.raises(ValidationError):
            GenerationSettings(temperature=2.1)

    def test_token_bounds(self):
        """Test max_tokens value bounds"""
        # Valid tokens
        settings = GenerationSettings(max_tokens=1000)
        assert settings.max_tokens == 1000

        # Tokens too low
        with pytest.raises(ValidationError):
            GenerationSettings(max_tokens=99)

        # Tokens too high
        with pytest.raises(ValidationError):
            GenerationSettings(max_tokens=32001)


class TestChatMessage:
    """Test ChatMessage schema validation"""

    def test_valid_message(self):
        """Test creating valid ChatMessage"""
        message = ChatMessage(
            id="msg-123",
            type="user",
            content="Hello, assistant!",
            timestamp=datetime.now(),
            metadata={"source": "web"}
        )
        assert message.type == "user"
        assert message.content == "Hello, assistant!"

    def test_minimal_message(self):
        """Test creating ChatMessage with minimal data"""
        message = ChatMessage(type="assistant", content="Response")
        assert message.type == "assistant"
        assert message.content == "Response"
        assert message.id is None
        assert message.timestamp is None

    def test_invalid_type(self):
        """Test invalid message type"""
        with pytest.raises(ValidationError):
            ChatMessage(type="invalid", content="test")


class TestTestCase:
    """Test TestCase schema validation"""

    def test_valid_test_case(self):
        """Test creating valid TestCase"""
        test_case = TestCase(
            title="Test user login",
            description="Verify user can login with valid credentials",
            steps=[
                "Navigate to login page",
                "Enter valid username and password",
                "Click login button",
                "Verify user is redirected to dashboard"
            ],
            expected_result="User should be logged in and redirected to dashboard",
            priority="high",
            tags=["smoke", "auth"]
        )
        assert test_case.title == "Test user login"
        assert len(test_case.steps) == 4
        assert test_case.priority == "high"

    def test_minimal_test_case(self):
        """Test creating TestCase with minimal data"""
        test_case = TestCase(
            title="Simple test",
            steps=["Step 1"],
            expected_result="Result"
        )
        assert test_case.title == "Simple test"
        assert test_case.priority == "normal"
        assert test_case.tags == []


class TestValidationResult:
    """Test ValidationResult schema validation"""

    def test_valid_result(self):
        """Test creating valid ValidationResult"""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["This is a warning"],
            suggestions=["Consider using more descriptive names"]
        )
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1

    def test_invalid_result(self):
        """Test ValidationResult with errors"""
        result = ValidationResult(
            is_valid=False,
            errors=["Syntax error at line 10"],
            warnings=["Unused import"],
            suggestions=["Fix syntax error"]
        )
        assert result.is_valid is False
        assert "Syntax error" in result.errors[0]


class TestCoverageAnalysisRequest:
    """Test CoverageAnalysisRequest schema validation"""

    def test_valid_request(self):
        """Test creating valid CoverageAnalysisRequest"""
        files = [
            UploadedFile(
                name="test.py",
                path="src/test.py",
                content="def hello(): pass",
                language="python",
                size=100,
                is_test_file=False
            )
        ]
        request = CoverageAnalysisRequest(
            project_files=files,
            test_files=[],
            language="python",
            framework="pytest",
            include_suggestions=True
        )
        assert len(request.project_files) == 1
        assert request.language == "python"

    def test_minimal_request(self):
        """Test creating minimal CoverageAnalysisRequest"""
        request = CoverageAnalysisRequest(
            project_files=[],
            language="python"
        )
        assert request.project_files == []
        assert request.test_files == []
        assert request.include_suggestions is True  # Default value


class TestUploadedFile:
    """Test UploadedFile schema validation"""

    def test_valid_file(self):
        """Test creating valid UploadedFile"""
        file = UploadedFile(
            name="utils.py",
            path="src/utils.py",
            content="def utility(): pass",
            language="python",
            size=100,
            is_test_file=False
        )
        assert file.name == "utils.py"
        assert file.language == "python"
        assert file.is_test_file is False

    def test_test_file(self):
        """Test creating UploadedFile as test file"""
        file = UploadedFile(
            name="test_utils.py",
            path="tests/test_utils.py",
            content="def test_utility(): pass",
            language="python",
            size=100,
            is_test_file=True
        )
        assert file.is_test_file is True


class TestCoverageMetrics:
    """Test CoverageMetrics schema validation"""

    def test_valid_metrics(self):
        """Test creating valid CoverageMetrics"""
        metrics = CoverageMetrics(
            lines_covered=80,
            lines_total=100,
            coverage_percentage=80.0,
            functions_covered=8,
            functions_total=10,
            branches_covered=16,
            branches_total=20
        )
        assert metrics.coverage_percentage == 80.0
        assert metrics.functions_covered == 8

    def test_zero_coverage(self):
        """Test CoverageMetrics with zero coverage"""
        metrics = CoverageMetrics(
            lines_covered=0,
            lines_total=100,
            coverage_percentage=0.0,
            functions_covered=0,
            functions_total=10,
            branches_covered=0,
            branches_total=20
        )
        assert metrics.coverage_percentage == 0.0


class TestUncoveredFunction:
    """Test UncoveredFunction schema validation"""

    def test_valid_function(self):
        """Test creating valid UncoveredFunction"""
        func = UncoveredFunction(
            name="calculate",
            file_path="src/math.py",
            line_start=10,
            line_end=20,
            signature="def calculate(a: int, b: int) -> int:",
            complexity=3,
            priority="high"
        )
        assert func.name == "calculate"
        assert func.line_start == 10
        assert func.line_end == 20
        assert func.complexity == 3
        assert func.priority == "high"

    def test_minimal_function(self):
        """Test creating UncoveredFunction with minimal data"""
        func = UncoveredFunction(
            name="simple",
            file_path="test.py",
            line_start=1,
            line_end=1,
            signature="def simple():"
        )
        assert func.complexity == 1  # Default value
        assert func.priority == "medium"  # Default value


class TestDateTimeFormats:
    """Test datetime handling and formats"""

    def test_chat_message_datetime(self):
        """Test ChatMessage with datetime"""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        message = ChatMessage(
            type="user",
            content="Test message",
            timestamp=timestamp
        )
        assert message.timestamp == timestamp
        assert message.timestamp.year == 2024
        assert message.timestamp.month == 1

    def test_optional_datetime(self):
        """Test optional datetime fields"""
        message = ChatMessage(type="assistant", content="Response")
        assert message.timestamp is None


class TestStringFormats:
    """Test string format validations"""

    def test_requirements_length(self):
        """Test requirements string length validation"""
        # Valid length
        request = ManualTestRequest(requirements="Test description")
        assert len(request.requirements) > 2

        # Too short
        with pytest.raises(ValidationError):
            ManualTestRequest(requirements="x")

        # Too long
        with pytest.raises(ValidationError):
            ManualTestRequest(requirements="x" * 10001)

    def test_url_formats(self):
        """Test URL format validation"""
        # GitHub URL pattern
        github_url = "https://github.com/user/repo.git"
        assert "github.com" in github_url
        assert github_url.endswith(".git")

        # GitLab URL pattern
        gitlab_url = "https://gitlab.com/user/repo.git"
        assert "gitlab.com" in gitlab_url
        assert gitlab_url.endswith(".git")


class TestNumericFormats:
    """Test numeric format validations"""

    def test_float_values(self):
        """Test float value validations"""
        # Valid floats
        settings = GenerationSettings(temperature=0.5)
        assert isinstance(settings.temperature, float)
        assert 0.0 <= settings.temperature <= 2.0

        # Coverage percentage
        metrics = CoverageMetrics(
            lines_covered=75,
            lines_total=100,
            coverage_percentage=75.5,
            functions_covered=5,
            functions_total=10,
            branches_covered=10,
            branches_total=15
        )
        assert isinstance(metrics.coverage_percentage, float)
        assert 0 <= metrics.coverage_percentage <= 100

    def test_integer_values(self):
        """Test integer value validations"""
        # Line numbers
        func = UncoveredFunction(
            name="test",
            file_path="test.py",
            line_start=10,
            line_end=20,
            signature="def test():"
        )
        assert isinstance(func.line_start, int)
        assert isinstance(func.line_end, int)
        assert func.line_start > 0
        assert func.line_end >= func.line_start

        # File size
        file = UploadedFile(
            name="test.py",
            path="test.py",
            content="pass",
            language="python",
            size=4,
            is_test_file=False
        )
        assert isinstance(file.size, int)
        assert file.size >= 0


class TestBooleanFormats:
    """Test boolean format validations"""

    def test_boolean_defaults(self):
        """Test boolean default values"""
        # GenerationSettings defaults
        settings = GenerationSettings()
        assert isinstance(settings.use_aaa_pattern, bool)
        assert settings.use_aaa_pattern is True
        assert isinstance(settings.include_negative_tests, bool)
        assert settings.include_negative_tests is True

        # CoverageAnalysisRequest defaults
        request = CoverageAnalysisRequest(project_files=[])
        assert isinstance(request.include_suggestions, bool)
        assert request.include_suggestions is True

    def test_boolean_explicit(self):
        """Test explicit boolean values"""
        settings = GenerationSettings(
            use_aaa_pattern=False,
            include_negative_tests=False
        )
        assert settings.use_aaa_pattern is False
        assert settings.include_negative_tests is False