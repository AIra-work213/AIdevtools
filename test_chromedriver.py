#!/usr/bin/env python3
"""Test ChromeDriver configuration in Docker"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os
import sys

def test_chromedriver():
    """Test if ChromeDriver is properly configured"""
    
    print("=== ChromeDriver Configuration Test ===\n")
    
    # Check environment variables
    print("Environment Variables:")
    print(f"  CHROME_BIN: {os.getenv('CHROME_BIN', 'Not set')}")
    print(f"  CHROMEDRIVER_PATH: {os.getenv('CHROMEDRIVER_PATH', 'Not set')}")
    print()
    
    # Check if ChromeDriver exists
    chromedriver_paths = [
        '/usr/lib/chromium/chromedriver',
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver'
    ]
    
    print("Checking ChromeDriver locations:")
    found_path = None
    for path in chromedriver_paths:
        exists = os.path.exists(path)
        print(f"  {path}: {'✓ Found' if exists else '✗ Not found'}")
        if exists and not found_path:
            found_path = path
    print()
    
    if not found_path:
        print("ERROR: ChromeDriver not found in any expected location!")
        return False
    
    # Try to initialize ChromeDriver
    print(f"Attempting to initialize ChromeDriver from: {found_path}")
    
    try:
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--window-size=1920,1080')
        
        service = Service(found_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        print("✓ ChromeDriver initialized successfully!")
        
        # Test navigation
        print("\nTesting navigation to example.com...")
        driver.get("https://example.com")
        title = driver.title
        print(f"✓ Page loaded successfully. Title: {title}")
        
        driver.quit()
        print("\n=== Test PASSED ===")
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to initialize ChromeDriver")
        print(f"  Exception: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        print("\n=== Test FAILED ===")
        return False

if __name__ == "__main__":
    success = test_chromedriver()
    sys.exit(0 if success else 1)
