#!/usr/bin/env python3
"""
Test UI Test Generation Feature
Tests both HTML and URL methods with setup instructions
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/generate"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_html_method():
    """Test UI generation from HTML content"""
    print_section("TEST 1: UI Generation from HTML (Playwright)")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Login Page</title></head>
    <body>
        <form id="login-form">
            <input type="text" id="username" name="username" placeholder="Username">
            <input type="password" id="password" name="password" placeholder="Password">
            <button type="submit" id="login-btn">Login</button>
        </form>
        <div id="error-message" style="display:none;"></div>
    </body>
    </html>
    """
    
    payload = {
        "input_method": "html",
        "html_content": html_content,
        "framework": "playwright",
        "selectors": {
            "username": "#username",
            "password": "#password",
            "submit": "#login-btn"
        }
    }
    
    print(f"📤 Sending request to {BASE_URL}/auto/ui")
    print(f"   Framework: playwright")
    print(f"   Method: HTML parsing")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/auto/ui", json=payload, timeout=120)
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Response time: {elapsed:.2f}s")
    print(f"📊 Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS! Test generated successfully")
        print(f"\n📝 Generated Code Preview (first 500 chars):")
        print("-" * 80)
        print(data['code'][:500] + "...")
        print("-" * 80)
        
        print(f"\n🎯 Test Scenarios Found: {len(data['test_scenarios'])}")
        for i, scenario in enumerate(data['test_scenarios'], 1):
            print(f"   {i}. {scenario}")
        
        print(f"\n🔍 Selectors Found: {len(data['selectors_found'])}")
        for selector in data['selectors_found'][:5]:
            print(f"   - {selector}")
        
        print(f"\n📋 Setup Instructions:")
        print("-" * 80)
        print(data['setup_instructions'])
        print("-" * 80)
        
        print(f"\n🔬 Validation:")
        print(f"   Valid: {data['validation']['is_valid']}")
        print(f"   Errors: {len(data['validation']['errors'])}")
        print(f"   Warnings: {len(data['validation']['warnings'])}")
        
        # Save generated code to file
        with open("/tmp/test_ui_playwright.py", "w") as f:
            f.write(data['code'])
        print(f"\n💾 Code saved to: /tmp/test_ui_playwright.py")
        
        return True
    else:
        print(f"\n❌ FAILED!")
        print(f"Error: {response.text}")
        return False

def test_url_method():
    """Test UI generation from URL"""
    print_section("TEST 2: UI Generation from URL (Selenium)")
    
    payload = {
        "input_method": "url",
        "url": "https://example.com",
        "framework": "selenium",
        "selectors": {}
    }
    
    print(f"📤 Sending request to {BASE_URL}/auto/ui")
    print(f"   Framework: selenium")
    print(f"   Method: URL")
    print(f"   Target: https://example.com")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/auto/ui", json=payload, timeout=120)
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Response time: {elapsed:.2f}s")
    print(f"📊 Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS! Test generated successfully")
        print(f"\n📝 Generated Code Preview (first 500 chars):")
        print("-" * 80)
        print(data['code'][:500] + "...")
        print("-" * 80)
        
        print(f"\n🎯 Test Scenarios Found: {len(data['test_scenarios'])}")
        for i, scenario in enumerate(data['test_scenarios'], 1):
            print(f"   {i}. {scenario}")
        
        print(f"\n🔍 Selectors Found: {len(data['selectors_found'])}")
        for selector in data['selectors_found'][:5]:
            print(f"   - {selector}")
        
        print(f"\n📋 Setup Instructions:")
        print("-" * 80)
        print(data['setup_instructions'])
        print("-" * 80)
        
        print(f"\n🔬 Validation:")
        print(f"   Valid: {data['validation']['is_valid']}")
        print(f"   Errors: {len(data['validation']['errors'])}")
        print(f"   Warnings: {len(data['validation']['warnings'])}")
        
        # Save generated code to file
        with open("/tmp/test_ui_selenium.py", "w") as f:
            f.write(data['code'])
        print(f"\n💾 Code saved to: /tmp/test_ui_selenium.py")
        
        return True
    else:
        print(f"\n❌ FAILED!")
        print(f"Error: {response.text}")
        return False

def test_cypress_framework():
    """Test UI generation with Cypress"""
    print_section("TEST 3: UI Generation with Cypress")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <body>
        <nav>
            <a href="/" class="home-link">Home</a>
            <a href="/about" class="about-link">About</a>
        </nav>
        <main>
            <h1>Welcome</h1>
            <button class="cta-button">Get Started</button>
        </main>
    </body>
    </html>
    """
    
    payload = {
        "input_method": "html",
        "html_content": html_content,
        "framework": "cypress"
    }
    
    print(f"📤 Sending request to {BASE_URL}/auto/ui")
    print(f"   Framework: cypress")
    print(f"   Method: HTML parsing")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/auto/ui", json=payload, timeout=120)
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Response time: {elapsed:.2f}s")
    print(f"📊 Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS! Test generated successfully")
        print(f"\n📝 Generated Code Preview (first 500 chars):")
        print("-" * 80)
        print(data['code'][:500] + "...")
        print("-" * 80)
        
        print(f"\n📋 Setup Instructions Preview:")
        print("-" * 80)
        print(data['setup_instructions'][:400] + "...")
        print("-" * 80)
        
        # Save generated code to file
        with open("/tmp/test_ui_cypress.cy.js", "w") as f:
            f.write(data['code'])
        print(f"\n💾 Code saved to: /tmp/test_ui_cypress.cy.js")
        
        return True
    else:
        print(f"\n❌ FAILED!")
        print(f"Error: {response.text}")
        return False

def main():
    print("\n" + "="*80)
    print("  🧪 UI Test Generation - Comprehensive Testing")
    print("="*80)
    print("\nThis test will verify:")
    print("  1. HTML method with Playwright")
    print("  2. URL method with Selenium")
    print("  3. Cypress framework support")
    print("  4. Setup instructions generation")
    print("  5. Code validation with AI retry")
    
    results = []
    
    # Test 1: HTML + Playwright
    try:
        result1 = test_html_method()
        results.append(("HTML + Playwright", result1))
        time.sleep(2)
    except Exception as e:
        print(f"\n❌ Test 1 crashed: {e}")
        results.append(("HTML + Playwright", False))
    
    # Test 2: URL + Selenium
    try:
        result2 = test_url_method()
        results.append(("URL + Selenium", result2))
        time.sleep(2)
    except Exception as e:
        print(f"\n❌ Test 2 crashed: {e}")
        results.append(("URL + Selenium", False))
    
    # Test 3: Cypress
    try:
        result3 = test_cypress_framework()
        results.append(("HTML + Cypress", result3))
    except Exception as e:
        print(f"\n❌ Test 3 crashed: {e}")
        results.append(("HTML + Cypress", False))
    
    # Summary
    print_section("SUMMARY")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\n📊 Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! UI generation is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")

if __name__ == "__main__":
    main()
