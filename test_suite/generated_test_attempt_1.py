import pytest
import allure
from allure_commons.types import Severity
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://www.python.org"


@pytest.fixture(scope="session")
def driver():
    options = Options()
    # Chrome binary location for headless Linux environments
    options.binary_location = "/snap/bin/chromium"
    # Headless and CI-friendly options
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    # Additional stability options
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # Disable images for faster loading
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--single-process")  # May help with memory issues
    # Initialize WebDriver
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)  # Increased to 60 seconds
    driver.implicitly_wait(20)  # Increased implicit wait to 20 seconds
    yield driver
    driver.quit()


@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
class TestUI:

    @allure.title("Verify page title contains welcome message")
    @allure.severity(allure.severity_level.NORMAL)
    def test_page_title(self, driver):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step("Verify page title contains expected text"):
            assert "Welcome to Python.org" in driver.title

    @allure.title("Verify 'Skip to content' link is present and correct")
    @allure.severity(allure.severity_level.NORMAL)
    def test_skip_to_content_link(self, driver):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step("Locate 'Skip to content' link"):
            skip_link = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.LINK_TEXT, "Skip to content"))
            )
        with allure.step("Verify the link is displayed"):
            assert skip_link.is_displayed()
        with allure.step("Verify the link href ends with '#content'"):
            href = skip_link.get_attribute("href")
            assert href.endswith("#content")

    @allure.title("Validate main navigation links hrefs")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "link_text,expected_href",
        [
            ("Python", "/"),
            ("PSF", "https://www.python.org/psf/"),
            ("Docs", "https://docs.python.org"),
            ("PyPI", None),
            ("Jobs", None),
            ("Community", None),
            ("Donate", None),
        ],
    )
    def test_main_navigation_links(self, driver, link_text, expected_href):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step(f"Locate navigation link with text '{link_text}'"):
            link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.LINK_TEXT, link_text))
            )
        with allure.step("Verify the link is displayed"):
            assert link.is_displayed()
        if expected_href:
            with allure.step(f"Verify link href ends with expected fragment '{expected_href}'"):
                href = link.get_attribute("href")
                assert href.endswith(expected_href)

    @allure.title("Search functionality returns results for query")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search_functionality(self, driver):
        query = "list comprehension"
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step("Locate the search input field"):
            search_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
        with allure.step(f"Enter text '{query}' into search field"):
            search_input.clear()
            search_input.send_keys(query)
        with allure.step("Submit the search form"):
            search_input.submit()
        with allure.step("Wait for results page title to contain 'Search'"):
            WebDriverWait(driver, 10).until(EC.title_contains("Search"))
        with allure.step("Verify the page title contains 'Search'"):
            assert "Search" in driver.title
        with allure.step("Verify the query appears in the page body"):
            body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            assert query.lower() in body_text

    @allure.title("Check paragraph excerpt contains expected snippet")
    @allure.severity(allure.severity_level.NORMAL)
    def test_paragraph_excerpt(self, driver):
        excerpt_snippet = "The core of extensible programming is defining functions"
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step("Locate paragraph containing the expected snippet (case‑insensitive)"):
            paragraph = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        f"//p[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
                        f"'{excerpt_snippet.lower()}')]",
                    )
                )
            )
        with allure.step("Verify the paragraph is displayed"):
            assert paragraph.is_displayed()
        with allure.step("Verify the paragraph text contains the exact snippet"):
            assert excerpt_snippet in paragraph.text