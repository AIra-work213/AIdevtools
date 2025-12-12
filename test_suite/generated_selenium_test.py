import pytest
import allure
from allure_commons.types import Severity
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://example.com"


@pytest.fixture(scope="function")
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

    @allure.title("Test Home Page Title")
    @allure.severity(Severity.NORMAL)
    def test_home_page_title(self, driver):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step("Verify page title contains 'Example Domain'"):
            assert "Example Domain" in driver.title

    @allure.title("Test Home Page Header")
    @allure.severity(Severity.NORMAL)
    def test_home_page_header(self, driver):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step("Interact with header element"):
            header = driver.find_element(By.TAG_NAME, "h1")
        with allure.step("Verify header is displayed and has correct text"):
            assert header.is_displayed()
            assert header.text == "Example Domain"

    @allure.title("Test More Information Link Navigation")
    @allure.severity(Severity.NORMAL)
    def test_more_information_link_navigation(self, driver):
        with allure.step(f"Navigate to {BASE_URL}"):
            driver.get(BASE_URL)
        with allure.step("Interact with 'More information...' link"):
            more_info_link = driver.find_element(By.XPATH, "//a[text()='More information...']")
            assert more_info_link.is_displayed()
            more_info_link.click()
        with allure.step("Verify navigation to IANA page"):
            WebDriverWait(driver, 10).until(EC.title_contains("IANA"))
            assert "IANA" in driver.title
        with allure.step("Verify the new page contains expected content"):
            body_text = driver.find_element(By.TAG_NAME, "body").text
            assert "Internet Assigned Numbers Authority" in body_text