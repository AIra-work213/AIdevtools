import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def verify_selenium():
    print("Starting Selenium Verification...")

    # Configure Chrome options
    options = Options()

    # Check for Chrome/Chromium in common locations
    chrome_paths = [
        "/snap/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/chrome",
        "/opt/google/chrome/chrome"
    ]

    chrome_bin = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_bin = path
            print(f"Found Chrome at: {chrome_bin}")
            break

    if chrome_bin:
        options.binary_location = chrome_bin

    # Check for ChromeDriver in snap
    chromedriver_paths = [
        "/snap/chromium/current/usr/lib/chromium-browser/chromedriver",
        "/snap/chromium/3313/usr/lib/chromium-browser/chromedriver",
        "/snap/bin/chromium.chromedriver",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver"
    ]

    chromedriver_path = None
    for path in chromedriver_paths:
        if os.path.exists(path):
            chromedriver_path = path
            print(f"Found ChromeDriver at: {chromedriver_path}")
            break

    if not chromedriver_path:
        print("ERROR: ChromeDriver not found!")
        sys.exit(1)

    # Make sure chromedriver is executable (skip if read-only)
    try:
        os.chmod(chromedriver_path, 0o755)
    except OSError:
        print(f"Note: Cannot change permissions for {chromedriver_path} (read-only filesystem)")

    # Add headless and other necessary options
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-dev-shm-usage')

    try:
        print("Initializing WebDriver...")
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        print("WebDriver initialized successfully.")

        print("Navigating to python.org...")
        driver.get("https://www.python.org")

        title = driver.title
        print(f"Page Title: {title}")

        if "Python" in title:
            print("SUCCESS: Selenium is working correctly!")

            # Additional test: Find and interact with an element
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            try:
                # Wait for and find the search input
                search_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
                print(f"✓ Found search input: {search_input.get_attribute('type')}")

                # Type in the search box
                search_input.send_keys("Selenium test")
                print("✓ Successfully typed in search box")

                # Get page URL to confirm navigation worked
                current_url = driver.current_url
                print(f"✓ Current URL: {current_url}")

                # Find the main navigation
                nav = driver.find_element(By.ID, "mainnav")
                print(f"✓ Found main navigation: {nav.tag_name}")

                # Count links on the page
                links = driver.find_elements(By.TAG_NAME, "a")
                print(f"✓ Found {len(links)} links on the page")

            except Exception as e:
                print(f"Note: Could not interact with some elements: {e}")

        else:
            print(f"WARNING: Title did not match expected. Got: {title}")

        driver.quit()
        print("Test completed successfully!")

    except Exception as e:
        print(f"FAILURE: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify_selenium()
