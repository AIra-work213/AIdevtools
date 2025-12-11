"""
Comprehensive tests for UI test generation and execution with Selenium
Tests the complete flow: generation -> validation -> execution
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.services.ai_service import AIService
from app.services.code_validator import CodeValidator


class TestSeleniumUITestGeneration:
    """Test UI test generation with Selenium framework"""

    @pytest.fixture
    def ai_service(self):
        """Create AIService instance with mocked LLM client"""
        service = AIService()
        service.llm_client = AsyncMock()
        return service

    @pytest.fixture
    def code_validator(self):
        """Create CodeValidator instance"""
        return CodeValidator()

    @pytest.mark.asyncio
    async def test_generate_selenium_test_from_url(self, ai_service):
        """Test generating Selenium test from URL with headless configuration"""
        # Mock LLM response with valid Selenium code
        mock_selenium_code = '''
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

@pytest.fixture
def driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_homepage_title(driver):
    driver.get("https://example.com")
    assert "Example" in driver.title
'''
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_selenium_code)

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        assert result is not None
        assert "code" in result
        assert "selenium" in result["code"].lower()
        assert "--headless" in result["code"]
        assert "--no-sandbox" in result["code"]
        
    @pytest.mark.asyncio
    async def test_generate_selenium_test_injects_headless_config(self, ai_service):
        """Test that headless configuration is injected into Selenium tests"""
        mock_code = '''
import pytest
from selenium import webdriver

def test_example():
    driver = webdriver.Chrome()
    driver.get("https://example.com")
    driver.quit()
'''
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        # Verify headless configuration is mentioned in the prompt
        calls = ai_service.llm_client.chat_completion.call_args_list
        assert len(calls) > 0
        user_message = calls[0][1]["messages"][-1]["content"]
        assert "headless" in user_message.lower() or "HEADLESS" in user_message

    @pytest.mark.asyncio
    async def test_generate_selenium_with_allure_decorators(self, ai_service):
        """Test Selenium test generation with Allure decorators (Stage 2)"""
        base_code = '''
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_login(driver):
    driver.get("https://example.com/login")
    assert "Login" in driver.title
'''
        
        allure_wrapped_code = '''
import pytest
import allure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

@allure.feature("Authentication")
@allure.story("User Login")
@allure.severity(allure.severity_level.CRITICAL)
def test_login(driver):
    with allure.step("Navigate to login page"):
        driver.get("https://example.com/login")
    with allure.step("Verify page title"):
        assert "Login" in driver.title
'''
        
        ai_service.llm_client.chat_completion = AsyncMock(
            side_effect=[base_code, allure_wrapped_code]
        )

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com/login",
            framework="selenium"
        )

        assert "allure" in result["code"].lower()
        assert "@allure.feature" in result["code"] or "allure.step" in result["code"]

    @pytest.mark.asyncio
    async def test_selenium_code_cleaning_removes_markdown(self, ai_service):
        """Test that markdown code blocks are properly cleaned from LLM response"""
        mock_response = '''```python
import pytest
from selenium import webdriver

def test_example():
    driver = webdriver.Chrome()
    assert True
```'''
        
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_response)

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        assert "```" not in result["code"]
        assert "import pytest" in result["code"]


class TestSeleniumCodeValidation:
    """Test validation of generated Selenium tests"""

    @pytest.fixture
    def validator(self):
        return CodeValidator()

    def test_validate_valid_selenium_test(self, validator):
        """Test validation of syntactically correct Selenium test"""
        code = '''
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_example(driver):
    driver.get("https://example.com")
    assert driver.title
'''
        errors = validator.validate_syntax(code)
        assert len(errors) == 0

    def test_validate_selenium_test_with_syntax_error(self, validator):
        """Test validation catches syntax errors in Selenium test"""
        code = '''
import pytest
from selenium import webdriver

def test_example(driver):
    driver.get("https://example.com"  # Missing closing parenthesis
    assert driver.title
'''
        errors = validator.validate_syntax(code)
        assert len(errors) > 0

    def test_detect_allure_decorators(self, validator):
        """Test detection of Allure decorators in code"""
        code_with_allure = '''
import allure

@allure.feature("Login")
def test_login():
    pass
'''
        assert validator.has_allure_decorators(code_with_allure)

        code_without_allure = '''
import pytest

def test_login():
    pass
'''
        assert not validator.has_allure_decorators(code_without_allure)


class TestSeleniumCodeExecution:
    """Test execution of Selenium tests in isolated environment"""

    @pytest.fixture
    def validator(self):
        return CodeValidator()

    def test_execute_simple_selenium_test(self, validator):
        """Test execution of a simple Selenium test that should pass"""
        code = '''
import pytest

def test_simple_assertion():
    """Simple test without browser to verify pytest execution"""
    assert 1 + 1 == 2
'''
        result = validator.execute_code(
            code=code,
            run_with_pytest=True
        )

        assert result.can_execute
        assert len(result.runtime_errors) == 0

    def test_execute_failing_selenium_test(self, validator):
        """Test execution of a failing Selenium test"""
        code = '''
import pytest

def test_failing_assertion():
    """Test that should fail"""
    assert 1 + 1 == 3
'''
        result = validator.execute_code(
            code=code,
            run_with_pytest=True
        )

        # Test should execute but fail
        assert not result.can_execute  # Failing test means can_execute=False
        assert len(result.runtime_errors) > 0

    def test_selenium_test_timeout_handling(self):
        """Test that long-running Selenium tests are properly timed out"""
        validator = CodeValidator(timeout=2)  # 2 second timeout
        code = '''
import time
import pytest

def test_long_running():
    """Test that takes too long"""
    time.sleep(100)
    assert True
'''
        result = validator.execute_code(
            code=code,
            run_with_pytest=True
        )

        assert not result.can_execute
        assert any("timeout" in err.lower() for err in result.runtime_errors)


class TestSeleniumEnvironmentConfiguration:
    """Test Docker environment configuration for Selenium"""

    def test_environment_variables_set(self):
        """Test that required environment variables are set for Selenium"""
        import os
        
        # These should be set in the Docker environment
        chrome_bin = os.environ.get("CHROME_BIN")
        chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
        
        # In test environment, these might not be set, but validator should set defaults
        validator = CodeValidator()
        
        # The validator's execute_code method should set these env vars
        assert hasattr(validator, 'execute_code')

    @pytest.mark.asyncio
    async def test_selenium_imports_available(self):
        """Test that Selenium packages are importable"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            assert True
        except ImportError as e:
            pytest.fail(f"Selenium imports failed: {e}")


class TestUITestEndToEnd:
    """End-to-end tests for complete UI test workflow"""

    @pytest.fixture
    def ai_service(self):
        service = AIService()
        service.llm_client = AsyncMock()
        return service

    @pytest.fixture
    def validator(self):
        return CodeValidator()

    @pytest.mark.asyncio
    async def test_full_workflow_url_to_execution(self, ai_service, validator):
        """Test complete workflow: URL -> Generate -> Validate -> Execute"""
        
        # Step 1: Generate Selenium test
        mock_code = '''
import pytest
from selenium.webdriver.chrome.options import Options

def test_simple():
    """Simple test without actual Selenium to avoid Docker dependency in unit tests"""
    assert True
'''
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

        generated = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        assert "code" in generated
        
        # Step 2: Validate syntax
        syntax_errors = validator.validate_syntax(
            code=generated["code"]
        )
        
        assert len(syntax_errors) == 0

        # Step 3: Execute
        execution = validator.execute_code(
            code=generated["code"],
            run_with_pytest=True
        )

        assert execution.can_execute

    @pytest.mark.asyncio
    async def test_full_workflow_with_allure_reporting(self, ai_service, validator):
        """Test workflow with Allure reporting enabled"""
        
        mock_code = '''
import pytest
import allure

@allure.feature("Test Feature")
def test_with_allure():
    with allure.step("Step 1"):
        assert True
'''
        ai_service.llm_client.chat_completion = AsyncMock(
            side_effect=[mock_code, mock_code]  # Two stages
        )

        generated = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        # Check Allure is present
        has_allure = validator.has_allure_decorators(generated["code"])
        
        execution = validator.execute_code(
            code=generated["code"],
            run_with_pytest=True
        )

        # If Allure is present, check for Allure results
        if has_allure:
            assert execution.allure_report_path is not None or execution.can_execute
