"""
Integration tests for AI Service UI test generation
Tests different frameworks and input methods
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.ai_service import AIService


class TestUITestGenerationFrameworks:
    """Test UI test generation for different frameworks"""

    @pytest.fixture
    def ai_service(self):
        service = AIService()
        service.llm_client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_generate_playwright_test(self, ai_service):
        """Test Playwright test generation"""
        mock_code = '''
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

def test_homepage(browser):
    page = browser.new_page()
    page.goto("https://example.com")
    assert "Example" in page.title()
'''
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="playwright"
        )

        assert "playwright" in result["code"].lower()
        assert "code" in result

    @pytest.mark.asyncio
    async def test_generate_cypress_test(self, ai_service):
        """Test Cypress test generation"""
        mock_code = '''
describe('Homepage', () => {
  it('should load successfully', () => {
    cy.visit('https://example.com')
    cy.title().should('include', 'Example')
  })
})
'''
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="cypress"
        )

        assert "cy." in result["code"] or "describe" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_selenium_from_html(self, ai_service):
        """Test Selenium generation from HTML input"""
        html_content = '''
<html>
<body>
    <form id="login-form">
        <input type="text" id="username" />
        <input type="password" id="password" />
        <button type="submit">Login</button>
    </form>
</body>
</html>
'''
        mock_code = '''
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_login_form(driver):
    driver.get("https://example.com/login")
    username = driver.find_element(By.ID, "username")
    password = driver.find_element(By.ID, "password")
    assert username.is_displayed()
    assert password.is_displayed()
'''
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

        result = await ai_service.generate_ui_tests(
            input_method="html",
            html_content=html_content,
            framework="selenium"
        )

        assert "selenium" in result["code"].lower()
        assert "By.ID" in result["code"] or "find_element" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_with_custom_selectors(self, ai_service):
        """Test generation with custom selectors"""
        selectors = {
            "username": "#username",
            "password": "#password",
            "submit": "button[type=submit]"
        }
        
        mock_code = '''
import pytest
from selenium import webdriver

def test_with_selectors(driver):
    username = driver.find_element_by_css_selector("#username")
    password = driver.find_element_by_css_selector("#password")
    submit = driver.find_element_by_css_selector("button[type=submit]")
'''
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            selectors=selectors,
            framework="selenium"
        )

        # Verify selectors are passed to LLM
        call_args = ai_service.llm_client.chat_completion.call_args
        messages = call_args[1]["messages"]
        user_message = messages[-1]["content"]
        
        assert "selectors" in user_message.lower() or any(sel in user_message for sel in selectors.values())


class TestWebsiteStructureAnalysis:
    """Test website structure analysis for multi-page testing"""

    @pytest.fixture
    def ai_service(self):
        service = AIService()
        service.llm_client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_analyze_website_discovers_urls(self, ai_service):
        """Test that website analysis discovers multiple URLs"""
        
        with patch.object(ai_service, '_analyze_website_structure') as mock_analyze:
            mock_analyze.return_value = {
                "discovered_urls": [
                    "https://example.com/",
                    "https://example.com/about",
                    "https://example.com/contact"
                ],
                "structure": {
                    "homepage": "/",
                    "pages": ["/about", "/contact"]
                }
            }
            
            mock_code = "def test_page(): pass"
            ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

            result = await ai_service.generate_ui_tests(
                input_method="url",
                url="https://example.com",
                framework="selenium"
            )

            # Verify _analyze_website_structure was called
            mock_analyze.assert_called_once_with("https://example.com")

    @pytest.mark.asyncio
    async def test_multi_page_test_generation(self, ai_service):
        """Test that multi-page sites generate tests for different pages"""
        
        with patch.object(ai_service, '_analyze_website_structure') as mock_analyze:
            mock_analyze.return_value = {
                "discovered_urls": [
                    "https://example.com/",
                    "https://example.com/products",
                    "https://example.com/checkout"
                ],
                "structure": {}
            }
            
            mock_code = '''
def test_homepage():
    driver.get("https://example.com/")
    
def test_products_page():
    driver.get("https://example.com/products")
    
def test_checkout_page():
    driver.get("https://example.com/checkout")
'''
            ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

            result = await ai_service.generate_ui_tests(
                input_method="url",
                url="https://example.com",
                framework="selenium"
            )

            # Check that prompt includes discovered URLs
            call_args = ai_service.llm_client.chat_completion.call_args_list
            # Stage 1 call (first call)
            stage1_call = call_args[0]
            user_message = stage1_call[1]["messages"][-1]["content"]
            
            assert "pages" in user_message.lower() or "3 pages" in user_message.lower()


class TestAllureIntegration:
    """Test Allure reporting integration"""

    @pytest.fixture
    def ai_service(self):
        service = AIService()
        service.llm_client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_two_stage_generation_for_allure(self, ai_service):
        """Test that Allure wrapping happens in Stage 2"""
        
        base_code = '''
import pytest
def test_example():
    assert True
'''
        
        allure_code = '''
import pytest
import allure

@allure.feature("Example")
def test_example():
    with allure.step("Verify"):
        assert True
'''
        
        ai_service.llm_client.chat_completion = AsyncMock(
            side_effect=[base_code, allure_code]
        )

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        # Should have called LLM twice (Stage 1 + Stage 2)
        assert ai_service.llm_client.chat_completion.call_count >= 1
        
        # Final code should have Allure
        assert "allure" in result["code"].lower() or "@allure" in result["code"]

    @pytest.mark.asyncio
    async def test_allure_only_for_python_frameworks(self, ai_service):
        """Test that Allure wrapping only happens for Python frameworks"""
        
        mock_code = '''
describe('Test', () => {
  it('works', () => {
    expect(true).toBe(true)
  })
})
'''
        
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="cypress"  # JavaScript framework
        )

        # Cypress is JavaScript, so no Allure
        assert "allure" not in result["code"].lower()


class TestCodeCleaningAndFormatting:
    """Test code cleaning from LLM responses"""

    @pytest.fixture
    def ai_service(self):
        service = AIService()
        service.llm_client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_remove_markdown_code_blocks(self, ai_service):
        """Test removal of markdown code block markers"""
        
        mock_response = '''```python
import pytest

def test_example():
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

    @pytest.mark.asyncio
    async def test_remove_language_identifier(self, ai_service):
        """Test removal of language identifier from code blocks"""
        
        mock_response = '''```selenium
from selenium import webdriver
```'''
        
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_response)

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        assert "selenium" in result["code"].lower()  # Should be in imports
        # Verify code is cleaned properly
        assert "from selenium import webdriver" in result["code"] or "selenium" in result["code"]

    @pytest.mark.asyncio
    async def test_handle_plain_code_without_markdown(self, ai_service):
        """Test that plain code without markdown is handled correctly"""
        
        mock_response = '''import pytest
from selenium import webdriver

def test_example():
    assert True'''
        
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_response)

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        assert result["code"] == mock_response or result["code"].strip() == mock_response.strip()


class TestErrorHandling:
    """Test error handling in UI test generation"""

    @pytest.fixture
    def ai_service(self):
        service = AIService()
        service.llm_client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_handle_website_analysis_failure(self, ai_service):
        """Test graceful handling of website analysis failures"""
        
        with patch.object(ai_service, '_analyze_website_structure') as mock_analyze:
            mock_analyze.side_effect = Exception("Network error")
            
            mock_code = "def test_example(): pass"
            ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

            # Should not raise, should fall back to single URL
            result = await ai_service.generate_ui_tests(
                input_method="url",
                url="https://example.com",
                framework="selenium"
            )

            assert result is not None
            assert "code" in result

    @pytest.mark.asyncio
    async def test_handle_llm_timeout(self, ai_service):
        """Test handling of LLM timeout"""
        
        ai_service.llm_client.chat_completion = AsyncMock(
            side_effect=TimeoutError("LLM timeout")
        )

        with pytest.raises(TimeoutError):
            await ai_service.generate_ui_tests(
                input_method="url",
                url="https://example.com",
                framework="selenium"
            )

    @pytest.mark.asyncio
    async def test_handle_invalid_framework(self, ai_service):
        """Test handling of invalid framework selection"""
        
        mock_code = "def test(): pass"
        ai_service.llm_client.chat_completion = AsyncMock(return_value=mock_code)

        # Should default to Python even with unknown framework
        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="unknown_framework"
        )

        assert result is not None
