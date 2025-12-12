import pytest
import allure
from allure_commons.types import Severity
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://example.com"
TIMEOUT = 10


@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
class UIAllureMeta:
    """Container class for Allure metadata (no test logic)."""
    pass


@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(2)
    yield driver
    driver.quit()


@allure.title("Validate that the page title matches the expected value")
@allure.severity(allure.severity_level.NORMAL)
def test_page_title(driver):
    with allure.step(f"Navigate to {BASE_URL}"):
        driver.get(BASE_URL)
    with allure.step("Verify page title is 'Example Domain'"):
        assert driver.title == "Example Domain"


@allure.title("Check that the main heading (h1) displays the correct text")
@allure.severity(allure.severity_level.NORMAL)
def test_main_heading(driver):
    with allure.step(f"Navigate to {BASE_URL}"):
        driver.get(BASE_URL)
    with allure.step("Locate the main heading (h1)"):
        heading = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
    with allure.step("Verify heading text is 'Example Domain'"):
        assert heading.text == "Example Domain"


@allure.title("Validate paragraph contents contain expected documentation text")
@allure.severity(allure.severity_level.NORMAL)
def test_paragraph_content(driver):
    with allure.step(f"Navigate to {BASE_URL}"):
        driver.get(BASE_URL)
    with allure.step("Locate all paragraph elements within the main div"):
        paragraphs = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div > p"))
        )
    with allure.step("Verify at least one paragraph contains the documentation disclaimer"):
        assert any(
            "This domain is for use in documentation examples without needing permission."
            in p.text
            for p in paragraphs
        )
    with allure.step("Verify at least one paragraph contains a 'Learn more' link text"):
        assert any("Learn more" in p.text for p in paragraphs)


@allure.title("Ensure the 'Learn more' link exists and has correct attributes")
@allure.severity(allure.severity_level.CRITICAL)
def test_learn_more_link(driver):
    with allure.step(f"Navigate to {BASE_URL}"):
        driver.get(BASE_URL)
    with allure.step("Locate the 'Learn more' link"):
        link = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Learn more"))
        )
    with allure.step("Verify link text is correct"):
        assert link.text == "Learn more"
    with allure.step("Verify link href points to the expected IANA page"):
        href = link.get_attribute("href")
        assert "iana.org/domains/example" in href