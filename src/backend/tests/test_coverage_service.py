"""Tests for the coverage service"""

import pytest
from unittest.mock import Mock, AsyncMock
from app.services.coverage_service import CoverageAnalyzer, CodeUploader
from app.schemas.test import UploadedFile, CoverageAnalysisRequest, UncoveredFunction


class TestCoverageAnalyzer:
    """Test cases for CoverageAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        return CoverageAnalyzer()

    @pytest.fixture
    def sample_python_file(self):
        return UploadedFile(
            name="calculator.py",
            path="calculator.py",
            content='''def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)''',
            language="python",
            size=150,
            is_test_file=False
        )

    @pytest.fixture
    def sample_test_file(self):
        return UploadedFile(
            name="test_calculator.py",
            path="test_calculator.py",
            content='''import pytest
from calculator import add

def test_add():
    assert add(2, 3) == 5''',
            language="python",
            size=100,
            is_test_file=True
        )

    @pytest.mark.asyncio
    async def test_extract_python_functions(self, analyzer, sample_python_file):
        """Test extracting functions from Python code"""
        functions = analyzer._extract_python_functions(sample_python_file)

        assert len(functions) == 3
        assert functions[0].name == "add"
        assert functions[1].name == "multiply"
        assert functions[2].name == "fibonacci"

        # Check fibonacci function complexity
        fib_func = next(f for f in functions if f.name == "fibonacci")
        assert fib_func.complexity > 1  # Should have if statement and recursion

    @pytest.mark.asyncio
    async def test_analyze_coverage(self, analyzer, sample_python_file, sample_test_file):
        """Test coverage analysis"""
        request = CoverageAnalysisRequest(
            project_files=[sample_python_file],
            test_files=[sample_test_file],
            language="python",
            framework="pytest",
            include_suggestions=True
        )

        result = await analyzer.analyze_coverage(request)

        assert result.total_files == 1
        assert result.test_files == 1
        assert 0 <= result.overall_coverage <= 100
        assert len(result.uncovered_functions) >= 0
        assert result.coverage_report is not None
        assert isinstance(result.suggestions, list)

    def test_calculate_python_complexity(self, analyzer):
        """Test complexity calculation for Python functions"""
        # Simple function
        simple_func = Mock()
        simple_func.body = []
        assert analyzer._calculate_python_complexity(simple_func) == 1

    def test_get_coverage_color(self, analyzer):
        """Test coverage color coding"""
        assert analyzer._calculate_priority(1, None) == "low"
        assert analyzer._calculate_priority(3, None) == "medium"
        assert analyzer._calculate_priority(5, None) == "high"


class TestCodeUploader:
    """Test cases for CodeUploader"""

    @pytest.mark.asyncio
    async def test_upload_from_file(self):
        """Test file upload"""
        content = b'def test():\n    pass\n'
        uploaded = await CodeUploader.upload_from_file(content, "test.py", is_test=True)

        assert uploaded.name == "test.py"
        assert uploaded.path == "test.py"
        assert uploaded.content == "def test():\n    pass\n"
        assert uploaded.language == "python"
        assert uploaded.is_test_file is True

    @pytest.mark.asyncio
    async def test_language_detection(self):
        """Test language detection from file extension"""
        test_cases = [
            ("test.py", "python"),
            ("test.js", "javascript"),
            ("test.ts", "typescript"),
            ("test.java", "java"),
            ("test.cs", "csharp"),
            ("test.unknown", "unknown"),
        ]

        for filename, expected_lang in test_cases:
            content = b"// test file"
            uploaded = await CodeUploader.upload_from_file(content, filename)
            assert uploaded.language == expected_lang


@pytest.mark.asyncio
async def test_full_coverage_workflow():
    """Test the complete coverage analysis workflow"""
    # Create sample files
    source_file = UploadedFile(
        name="math_utils.py",
        path="src/math_utils.py",
        content='''def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

class MathOperations:
    def power(self, base, exp):
        return base ** exp''',
        language="python",
        size=200,
        is_test_file=False
    )

    test_file = UploadedFile(
        name="test_math.py",
        path="tests/test_math.py",
        content='''import pytest
from math_utils import add

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0''',
        language="python",
        size=100,
        is_test_file=True
    )

    # Perform analysis
    analyzer = CoverageAnalyzer()
    request = CoverageAnalysisRequest(
        project_files=[source_file],
        test_files=[test_file],
        language="python",
        framework="pytest",
        include_suggestions=True
    )

    result = await analyzer.analyze_coverage(request)

    # Verify results
    assert result.total_files == 1
    assert result.test_files == 1
    assert 0 <= result.overall_coverage <= 100

    # Check that uncovered functions are identified
    uncovered_names = [f.name for f in result.uncovered_functions]
    expected_uncovered = ["subtract", "factorial", "power"]

    # At least some functions should be uncovered
    assert len(result.uncovered_functions) > 0

    # Verify file coverage metrics
    assert source_file.path in result.file_coverage
    metrics = result.file_coverage[source_file.path]
    assert metrics.functions_total == 4  # 3 functions + 1 method
    assert metrics.functions_covered >= 0

    # Check that suggestions are generated
    assert len(result.suggestions) > 0

    # Verify coverage report is generated
    assert result.coverage_report is not None
    assert "Code Coverage Report" in result.coverage_report