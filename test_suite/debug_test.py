import pytest
import allure
from allure_commons.types import Severity
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://example.com"
EXPECTED_TITLE = "Example Domain"
EXPECTED_HEADING = "Example Domain"
EXPECTED_PARAGRAPHS = [
    "This domain is for use in documentation examples without needing permission. Avoid use in operations",
    "Learn more"
]
LINK_TEXT = "Learn more"
LINK_HREF = "https://iana.org/domains/example"


@pytest.fixture(scope="session")
def driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
class TestUI:

    @allure.title("Verify page title matches expected")
    @allure.severity(allure.severity_level.NORMAL)
    def test_page_title(self, driver):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step(f"Verify page title is '{EXPECTED_TITLE}'"):
            assert driver.title == EXPECTED_TITLE, f"Expected title '{EXPECTED_TITLE}' but got '{driver.title}'"

    @allure.title("Verify main heading text")
    @allure.severity(allure.severity_level.NORMAL)
    def test_main_heading(self, driver):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step("Locate main heading (h1)"):
            heading = driver.find_element(By.TAG_NAME, "h1")
        with allure.step(f"Verify heading text is '{EXPECTED_HEADING}'"):
            assert heading.text.strip() == EXPECTED_HEADING, f"Expected heading '{EXPECTED_HEADING}' but got '{heading.text}'"

    @allure.title("Verify expected paragraphs are present")
    @allure.severity(allure.severity_level.NORMAL)
    def test_paragraph_contents(self, driver):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step("Collect all paragraph texts"):
            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            paragraph_texts = [p.text.strip() for p in paragraphs]
        for expected in EXPECTED_PARAGRAPHS:
            with allure.step(f"Verify paragraph containing '{expected}' is present"):
                assert any(expected in txt for txt in paragraph_texts), f"Paragraph containing '{expected}' not found"

    @allure.title("Verify 'Learn more' link is displayed with correct href")
    @allure.severity(allure.severity_level.NORMAL)
    def test_learn_more_link_presence(self, driver):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step(f"Locate link with text '{LINK_TEXT}'"):
            link = driver.find_element(By.LINK_TEXT, LINK_TEXT)
        with allure.step("Verify link is displayed"):
            assert link.is_displayed(), "Learn more link is not displayed"
        with allure.step(f"Verify link href equals '{LINK_HREF}'"):
            href = link.get_attribute("href")
            assert href == LINK_HREF, f"Expected href '{LINK_HREF}' but got '{href}'"

    @allure.title("Verify navigation via 'Learn more' link to IANA page")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_learn_more_link_navigation(self, driver):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step(f"Locate link with text '{LINK_TEXT}'"):
            link = driver.find_element(By.LINK_TEXT, LINK_TEXT)
        with allure.step(f"Click '{LINK_TEXT}' link"):
            link.click()
        with allure.step("Wait for new page title to contain 'IANA'"):
            WebDriverWait(driver, 10).until(EC.title_contains("IANA"))
        with allure.step(f"Verify current URL contains expected href '{LINK_HREF}'"):
            assert LINK_HREF in driver.current_url, f"Expected to navigate to '{LINK_HREF}' but landed on '{driver.current_url}'"
        with allure.step("Verify new page title contains 'IANA'"):
            assert "IANA" in driver.title, f"Expected new page title to contain 'IANA' but got '{driver.title}'"