#!/usr/bin/env python3
"""
Comprehensive UI Test for Python.org using Selenium with Allure reporting
"""
import pytest
import allure
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


@allure.feature("Python.org UI Testing")
@allure.story("Main Page Functionality")
@allure.severity(allure.severity_level.CRITICAL)
class TestPythonOrgUI:

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test"""
        # Setup
        self.options = Options()
        self.options.add_argument('--headless=new')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--remote-debugging-port=9222')

        # Chrome binary location
        self.options.binary_location = "/snap/bin/chromium"

        # ChromeDriver path
        chromedriver_path = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"
        self.service = Service(executable_path=chromedriver_path)

        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        self.driver.implicitly_wait(10)
        self.base_url = "https://www.python.org"

        yield

        # Teardown
        self.driver.quit()

    @allure.title("Navigate to Python.org and verify title")
    @allure.description("Test navigation to python.org and verify the page title")
    @allure.tag("smoke", "navigation")
    def test_page_title_and_navigation(self):
        """Test that the page loads and has the correct title"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        with allure.step("Verify page title"):
            title = self.driver.title
            allure.attach(title, name="Page Title", attachment_type=allure.attachment_type.TEXT)
            assert "Python" in title, f"Expected 'Python' in title, got '{title}'"

    @allure.title("Verify main navigation menu")
    @allure.description("Test that the main navigation menu is present and functional")
    @allure.tag("navigation", "menu")
    def test_main_navigation(self):
        """Test the main navigation menu"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        with allure.step("Find main navigation"):
            nav = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "mainnav"))
            )
            assert nav.is_displayed(), "Main navigation is not visible"

        with allure.step("Count navigation links"):
            nav_links = nav.find_elements(By.TAG_NAME, "a")
            allure.attach(str(len(nav_links)), name="Navigation Links Count", attachment_type=allure.attachment_type.TEXT)
            assert len(nav_links) > 0, "No navigation links found"

            # Take screenshot
            allure.attach(self.driver.get_screenshot_as_png(),
                         name="Navigation Menu",
                         attachment_type=allure.attachment_type.PNG)

    @allure.title("Search functionality test")
    @allure.description("Test the search functionality with different queries")
    @allure.tag("search", "input")
    def test_search_functionality(self):
        """Test the search functionality"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        with allure.step("Find search input"):
            search_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
            assert search_input.is_displayed(), "Search input is not visible"

        with allure.step("Enter search query"):
            search_query = "python selenium"
            search_input.send_keys(search_query)
            allure.attach(search_query, name="Search Query", attachment_type=allure.attachment_type.TEXT)

        with allure.step("Submit search"):
            search_input.submit()

        with allure.step("Verify search results"):
            WebDriverWait(self.driver, 10).until(
                lambda driver: "search" in driver.current_url.lower() or
                              len(driver.find_elements(By.CSS_SELECTOR, ".search-result")) > 0
            )

            # Take screenshot of results
            allure.attach(self.driver.get_screenshot_as_png(),
                         name="Search Results",
                         attachment_type=allure.attachment_type.PNG)

    @allure.title("Download page link verification")
    @allure.description("Test that the Downloads page link works correctly")
    @allure.tag("navigation", "download")
    def test_download_page_link(self):
        """Test navigation to the Downloads page"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        with allure.step("Find and click Downloads link"):
            downloads_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Downloads"))
            )
            downloads_link.click()

        with allure.step("Verify Downloads page"):
            WebDriverWait(self.driver, 10).until(
                EC.title_contains("Download")
            )

            current_url = self.driver.current_url
            allure.attach(current_url, name="Downloads URL", attachment_type=allure.attachment_type.TEXT)
            assert "downloads" in current_url.lower(), "Not on Downloads page"

            # Take screenshot
            allure.attach(self.driver.get_screenshot_as_png(),
                         name="Downloads Page",
                         attachment_type=allure.attachment_type.PNG)

    @allure.title("Documentation page access")
    @allure.description("Test navigation to the Documentation page")
    @allure.tag("navigation", "documentation")
    def test_documentation_page(self):
        """Test navigation to the Documentation page"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        with allure.step("Find and click Documentation link"):
            doc_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Documentation"))
            )
            doc_link.click()

        with allure.step("Verify Documentation page"):
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("docs")
            )

            current_url = self.driver.current_url
            allure.attach(current_url, name="Documentation URL", attachment_type=allure.attachment_type.TEXT)
            assert "docs" in current_url.lower(), "Not on Documentation page"

            # Take screenshot
            allure.attach(self.driver.get_screenshot_as_png(),
                         name="Documentation Page",
                         attachment_type=allure.attachment_type.PNG)

    @allure.title("PSF Community page access")
    @allure.description("Test navigation to the PSF/Community page")
    @allure.tag("navigation", "community")
    def test_community_page(self):
        """Test navigation to the Community page"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        with allure.step("Find and click Community link"):
            community_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Community"))
            )
            community_link.click()

        with allure.step("Verify Community page"):
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("psf") or EC.url_contains("community")
            )

            current_url = self.driver.current_url
            allure.attach(current_url, name="Community URL", attachment_type=allure.attachment_type.TEXT)
            assert "psf" in current_url.lower() or "community" in current_url.lower(), "Not on Community page"

            # Take screenshot
            allure.attach(self.driver.get_screenshot_as_png(),
                         name="Community Page",
                         attachment_type=allure.attachment_type.PNG)

    @allure.title("Events Blog link verification")
    @allure.description("Test navigation to the Events/Blog page")
    @allure.tag("navigation", "blog", "events")
    def test_events_blog_page(self):
        """Test navigation to the Events/Blog page"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        with allure.step("Find and click Blog link"):
            try:
                blog_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Blog"))
                )
            except:
                # Try alternative link text
                blog_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Events"))
                )
            blog_link.click()

        with allure.step("Verify Blog/Events page"):
            time.sleep(2)  # Wait for page to load
            current_url = self.driver.current_url
            allure.attach(current_url, name="Blog/Events URL", attachment_type=allure.attachment_type.TEXT)

            # Take screenshot
            allure.attach(self.driver.get_screenshot_as_png(),
                         name="Blog/Events Page",
                         attachment_type=allure.attachment_type.PNG)

    @allure.title("Python Logo visibility")
    @allure.description("Test that the Python logo is visible on the page")
    @allure.tag("ui", "branding")
    def test_python_logo(self):
        """Test that the Python logo is displayed"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        with allure.step("Find Python logo"):
            logo = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".python-logo, #python-logo, img[alt*='Python']"))
            )
            assert logo.is_displayed(), "Python logo is not visible"

            # Take screenshot
            allure.attach(self.driver.get_screenshot_as_png(),
                         name="Python Logo",
                         attachment_type=allure.attachment_type.PNG)

    @allure.title("Footer links verification")
    @allure.description("Test that footer contains important links")
    @allure.tag("footer", "links")
    def test_footer_links(self):
        """Test footer links"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        with allure.step("Find footer"):
            footer = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "footer"))
            )

        with allure.step("Count footer links"):
            footer_links = footer.find_elements(By.TAG_NAME, "a")
            allure.attach(str(len(footer_links)), name="Footer Links Count", attachment_type=allure.attachment_type.TEXT)
            assert len(footer_links) > 0, "No footer links found"

        with allure.step("Check for important links"):
            link_texts = [link.text.lower() for link in footer_links if link.text]
            important_links = ["privacy", "cookies", "terms", "trademarks"]

            for important in important_links:
                if any(important in text for text in link_texts):
                    allure.attach(important, name="Found Important Link", attachment_type=allure.attachment_type.TEXT)

            # Take screenshot of footer
            allure.attach(self.driver.get_screenshot_as_png(),
                         name="Footer",
                         attachment_type=allure.attachment_type.PNG)

    @allure.title("Responsive design test")
    @allure.description("Test page in different viewport sizes")
    @allure.tag("responsive", "design")
    def test_responsive_design(self):
        """Test responsive design by changing viewport size"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        # Test different screen sizes
        screen_sizes = [
            (1920, 1080, "Desktop"),
            (768, 1024, "Tablet"),
            (375, 812, "Mobile")
        ]

        for width, height, name in screen_sizes:
            with allure.step(f"Test {name} view ({width}x{height})"):
                self.driver.set_window_size(width, height)
                time.sleep(1)

                # Check if navigation is still visible
                try:
                    nav = self.driver.find_element(By.ID, "mainnav")
                    is_nav_visible = nav.is_displayed()
                except:
                    is_nav_visible = False

                allure.attach(f"Navigation visible: {is_nav_visible}",
                            name=f"{name} Navigation Status",
                            attachment_type=allure.attachment_type.TEXT)

                # Take screenshot
                allure.attach(self.driver.get_screenshot_as_png(),
                             name=f"{name} View",
                             attachment_type=allure.attachment_type.PNG)

    @allure.title("Interactive elements test")
    @allure.description("Test interactive elements like buttons and dropdowns")
    @allure.tag("interactive", "elements")
    def test_interactive_elements(self):
        """Test interactive elements on the page"""
        with allure.step("Navigate to python.org"):
            self.driver.get(self.base_url)

        with allure.step("Find all interactive elements"):
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            selects = self.driver.find_elements(By.TAG_NAME, "select")

            total_interactive = len(buttons) + len(inputs) + len(selects)
            allure.attach(str(total_interactive), name="Total Interactive Elements", attachment_type=allure.attachment_type.TEXT)

        with allure.step("Test hover effects on navigation"):
            try:
                nav_links = self.driver.find_elements(By.CSS_SELECTOR, "#mainnav a")
                if nav_links:
                    actions = ActionChains(self.driver)
                    first_link = nav_links[0]
                    actions.move_to_element(first_link).perform()
                    time.sleep(0.5)

                    # Take screenshot with hover
                    allure.attach(self.driver.get_screenshot_as_png(),
                                 name="Navigation Hover",
                                 attachment_type=allure.attachment_type.PNG)
            except Exception as e:
                allure.attach(str(e), name="Hover Test Note", attachment_type=allure.attachment_type.TEXT)


@allure.feature("Python.org Performance")
@allure.story("Page Load Performance")
class TestPythonOrgPerformance:

    @allure.title("Page load performance test")
    @allure.description("Measure page load times")
    @allure.tag("performance", "timing")
    def test_page_load_performance(self):
        """Test page load performance"""
        # Setup similar to above
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.binary_location = "/snap/bin/chromium"

        chromedriver_path = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"
        service = Service(executable_path=chromedriver_path)

        driver = webdriver.Chrome(service=service, options=options)

        try:
            with allure.step("Measure page load time"):
                start_time = time.time()
                driver.get("https://www.python.org")

                # Wait for main navigation to be present
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "mainnav"))
                )

                load_time = time.time() - start_time
                allure.attach(f"{load_time:.2f} seconds",
                            name="Page Load Time",
                            attachment_type=allure.attachment_type.TEXT)

                # Performance criteria
                assert load_time < 10, f"Page load time {load_time:.2f}s is too long"

        finally:
            driver.quit()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--alluredir=allure-results"])