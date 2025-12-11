import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def verify_selenium():
    print("Starting Selenium Verification...")
    
    # Paths found in the current environment
    chrome_bin = "/snap/bin/chromium"
    chromedriver_path = "/snap/bin/chromium.chromedriver"
    
    print(f"Chrome Binary: {chrome_bin}")
    print(f"ChromeDriver: {chromedriver_path}")
    
    if not os.path.exists(chrome_bin):
        print(f"ERROR: Chrome binary not found at {chrome_bin}")
        sys.exit(1)
        
    if not os.path.exists(chromedriver_path):
        print(f"ERROR: ChromeDriver not found at {chromedriver_path}")
        sys.exit(1)

    options = Options()
    options.binary_location = chrome_bin
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    service = Service(executable_path=chromedriver_path)
    
    try:
        print("Initializing WebDriver...")
        driver = webdriver.Chrome(service=service, options=options)
        print("WebDriver initialized successfully.")
        
        print("Navigating to python.org...")
        driver.get("https://www.python.org")
        
        title = driver.title
        print(f"Page Title: {title}")
        
        if "Python" in title:
            print("SUCCESS: Selenium is working correctly!")
        else:
            print("WARNING: Title did not match expected.")
            
        driver.quit()
        
    except Exception as e:
        print(f"FAILURE: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify_selenium()
