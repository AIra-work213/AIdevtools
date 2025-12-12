#!/usr/bin/env python3
"""
Quick test to verify requirements_file is in response
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/generate"

payload = {
    "input_method": "html",
    "html_content": "<button id='test'>Click me</button>",
    "framework": "playwright"
}

print("Testing UI generation with requirements_file field...")
response = requests.post(f"{BASE_URL}/auto/ui", json=payload, timeout=60)

if response.status_code == 200:
    data = response.json()
    
    print("\n✅ Response fields:")
    for key in data.keys():
        print(f"  - {key}")
    
    if 'requirements_file' in data:
        print("\n✅ requirements_file field present!")
        print("\n📦 Requirements content:")
        print("-" * 80)
        print(data['requirements_file'])
        print("-" * 80)
        
        # Save to file
        with open("/tmp/requirements_playwright.txt", "w") as f:
            f.write(data['requirements_file'])
        print("\n💾 Saved to /tmp/requirements_playwright.txt")
    else:
        print("\n❌ requirements_file field MISSING!")
else:
    print(f"\n❌ Request failed: {response.status_code}")
    print(response.text)
