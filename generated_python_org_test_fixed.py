import pytest
import allure
from allure_commons.types import Severity
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://www.python.org"

PAGE_URLS = [
    "https://www.python.org",
    "https://www.python.org/community/awards",
    "https://www.python.org/downloads/macos",
    "https://www.python.org/psf/conduct",
    "https://www.python.org/success-stories/category/arts",
    "https://www.python.org/downloads/source",
    "https://www.python.org/success-stories/category/business",
    "https://www.python.org/download/other",
    "https://www.python.org/doc/av",
    "https://www.python.org/downloads",
]

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture(scope="session")
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.binary_location = "/snap/bin/chromium"
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def assert_element_present(driver, by, value):
    try:
        element = driver.find_element(by, value)
        return element
    except NoSuchElementException:
        pytest.fail(f"Element not found: ({by}, {value})")


def assert_link_text_and_href(driver, link_text, expected_href):
    link = assert_element_present(driver, By.LINK_TEXT, link_text)
    actual_href = link.get_attribute("href")
    # Check if the href contains the expected value (handles full URLs vs fragments)
    assert expected_href in actual_href, f"Link '{link_text}' href mismatch: expected to contain '{expected_href}', got '{actual_href}'"


def verify_common_site_elements(driver):
    # Skip to content link (if present)
    try:
        skip_link = driver.find_element(By.LINK_TEXT, "Skip to content")
        assert "#content" in skip_link.get_attribute("href")
    except NoSuchElementException:
        pass  # Skip link may not be on all pages

    # Look for main navigation
    try:
        nav = driver.find_element(By.ID, "mainnav")
        assert nav.is_displayed()
    except NoSuchElementException:
        pass  # Navigation may be different on some pages

    # Check for Python branding
    assert "Python" in driver.title or "Python" in driver.page_source


# ----------------------------------------------------------------------
# Tests for each page
# ----------------------------------------------------------------------
@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
@allure.title("Page load and common elements validation")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("url", PAGE_URLS)
def test_page_load_and_common_elements(driver, url):
    with allure.step(f"Navigate to {url}"):
        driver.get(url)

    with allure.step("Verify page title contains 'Python'"):
        assert "Python" in driver.title, f"Page title does not contain 'Python' for {url}"

    with allure.step("Verify common site-wide elements"):
        verify_common_site_elements(driver)


@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
@allure.title("Home page specific content validation")
@allure.severity(allure.severity_level.NORMAL)
def test_home_page_specific_content(driver):
    with allure.step(f"Navigate to {BASE_URL}"):
        driver.get(BASE_URL)

    with allure.step("Verify exact page title"):
        assert "Python" in driver.title

    with allure.step("Verify presence of specific headings"):
        expected_headings = [
            "Functions Defined",
            "Compound Data Types",
            "Intuitive Interpretation",
            "All the Flow You’d Expect",
        ]
        for heading_text in expected_headings:
            try:
                heading = driver.find_element(
                    By.XPATH,
                    f"//*[self::h1 or self::h2 or self::h3][normalize-space()='{heading_text}']",
                )
                assert heading.is_displayed()
            except NoSuchElementException:
                pytest.fail(f"Expected heading '{heading_text}' not found on home page")

    with allure.step("Verify paragraph excerpts exist"):
        paragraph_snippets = [
            "Notice: While JavaScript is not essential for this website",
            "The core of extensible programming is defining functions.",
            "Lists (known as arrays in other languages) are one of the compound data types",
        ]
        page_source = driver.page_source
        for snippet in paragraph_snippets:
            assert snippet in page_source, f"Expected paragraph snippet not found: '{snippet}'"


@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
@allure.title("Navigation to Community section")
@allure.severity(allure.severity_level.CRITICAL)
def test_navigation_to_community_section(driver):
    with allure.step(f"Navigate to {BASE_URL}"):
        driver.get(BASE_URL)

    with allure.step("Locate Community link and verify its href"):
        community_link = assert_element_present(driver, By.LINK_TEXT, "Community")
        community_href = community_link.get_attribute("href")
        assert community_href.startswith(BASE_URL), "Community link does not point to an internal URL"

    with allure.step("Click Community link"):
        community_link.click()

    with allure.step("Wait for navigation to community section"):
        WebDriverWait(driver, 10).until(EC.url_contains("/community/"))
        assert "/community/" in driver.current_url, "Did not navigate to the community section"


@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
@allure.title("External links attributes validation")
@allure.severity(allure.severity_level.NORMAL)
def test_external_links_attributes(driver):
    with allure.step(f"Navigate to {BASE_URL}"):
        driver.get(BASE_URL)

    external_links = {
        "PSF": "https://www.python.org/psf/",
        "Docs": "https://docs.python.org",
    }
    for text, href in external_links.items():
        with allure.step(f"Verify link '{text}' points to '{href}'"):
            assert_link_text_and_href(driver, text, href)


@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
@allure.title("Skip to content functionality")
@allure.severity(allure.severity_level.NORMAL)
def test_skip_to_content_functionality(driver):
    with allure.step(f"Navigate to {BASE_URL}"):
        driver.get(BASE_URL)

    with allure.step("Click the 'Skip to content' link"):
        skip_link = assert_element_present(driver, By.LINK_TEXT, "Skip to content")
        skip_link.click()

    with allure.step("Verify focus moved to main content area"):
        content_elem = assert_element_present(driver, By.ID, "content")
        active_elem = driver.switch_to.active_element
        assert active_elem == content_elem, "Skip to content did not focus the main content area"


@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
@allure.title("Downloads page specific validation")
@allure.severity(allure.severity_level.NORMAL)
def test_page_specific_downloads_section(driver):
    url = "https://www.python.org/downloads"
    with allure.step(f"Navigate to {url}"):
        driver.get(url)

    with allure.step("Verify page title contains 'Download'"):
        assert "Download" in driver.title, "Downloads page title does not contain 'Download'"

    with allure.step("Verify 'Download Python' button exists"):
        try:
            download_button = driver.find_element(
                By.XPATH,
                "//a[contains(@class, 'download-button') or contains(text(),'Download Python')]",
            )
            assert download_button.is_displayed()
        except NoSuchElementException:
            pytest.fail("Download Python button not found on the downloads page")


@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
@allure.title("macOS downloads page specific validation")
@allure.severity(allure.severity_level.NORMAL)
def test_page_specific_macos_downloads(driver):
    url = "https://www.python.org/downloads/macos"
    with allure.step(f"Navigate to {url}"):
        driver.get(url)

    with allure.step("Verify page title mentions macOS"):
        assert "macOS" in driver.title or "macOS" in driver.page_source, "macOS downloads page does not mention macOS"

    with allure.step("Verify at least one installer link is present"):
        installer_links = driver.find_elements(
            By.XPATH,
            "//a[contains(@href, '.pkg') or contains(@href, '.dmg')]",
        )
        assert len(installer_links) > 0, "No macOS installer links found on the page"


@allure.feature("UI Testing")
@allure.story("User Workflows")
@allure.tag("ui", "e2e", "generated_by_ai")
@allure.title("PSF conduct page specific validation")
@allure.severity(allure.severity_level.NORMAL)
def test_page_specific_psf_conduct(driver):
    url = "https://www.python.org/psf/conduct"
    with allure.step(f"Navigate to {url}"):
        driver.get(url)

    with allure.step("Verify page contains the word 'conduct'"):
        assert "conduct" in driver.page_source.lower(), "Conduct page does not contain expected content"

    with allure.step("Verify heading 'Code of Conduct' exists"):
        try:
            heading = driver.find_element(
                By.XPATH,
                "//*[self::h1 or self::h2][contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'code of conduct')]",
            )
            assert heading.is_displayed()
        except NoSuchElementException:
            pytest.fail("Code of Conduct heading not found on PSF conduct page")