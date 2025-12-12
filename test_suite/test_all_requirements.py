#!/usr/bin/env python3
"""
Test requirements generation for all frameworks
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/generate"

frameworks = ["playwright", "selenium", "cypress"]

print("="*80)
print("  Testing Requirements Generation for All Frameworks")
print("="*80)

for framework in frameworks:
    print(f"\n📦 Testing {framework.upper()}...")
    
    payload = {
        "input_method": "html",
        "html_content": "<button id='test'>Click</button>",
        "framework": framework
    }
    
    response = requests.post(f"{BASE_URL}/auto/ui", json=payload, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        
        if 'requirements_file' in data:
            print(f"✅ Requirements generated!")
            print(f"\n{data['requirements_file']}")
            print("-" * 80)
            
            # Save to file
            filename = f"/tmp/requirements_{framework}.txt"
            with open(filename, "w") as f:
                f.write(data['requirements_file'])
            print(f"💾 Saved to {filename}\n")
        else:
            print(f"❌ No requirements_file in response!")
    else:
        print(f"❌ Request failed: {response.status_code}")

print("\n" + "="*80)
print("  ✅ All Requirements Files Generated!")
print("="*80)
print("\nFiles saved to:")
print("  - /tmp/requirements_playwright.txt")
print("  - /tmp/requirements_selenium.txt")
print("  - /tmp/requirements_cypress.txt")
