#!/usr/bin/env python3
"""
Test script to verify the code coverage analysis feature works correctly.
"""

import requests
import json
import tempfile
import os
from pathlib import Path

# API base URL
API_BASE = "http://localhost:8001/api/v1"

# Test Python code with various functions
PYTHON_CODE = '''
def add(a, b):
    """Add two numbers"""
    return a + b

def multiply(a, b):
    """Multiply two numbers"""
    return a * b

def fibonacci(n):
    """Calculate Fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def is_prime(n):
    """Check if number is prime"""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    w = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += w
        w = 6 - w
    return True

class Calculator:
    """Simple calculator class"""

    def __init__(self):
        self.history = []

    def calculate(self, operation, a, b):
        """Perform calculation and store in history"""
        result = None
        if operation == 'add':
            result = add(a, b)
        elif operation == 'multiply':
            result = multiply(a, b)

        if result is not None:
            self.history.append(f"{operation}({a}, {b}) = {result}")

        return result
'''

# Test file with partial coverage
TEST_CODE = '''
import pytest
from calculator import add, multiply

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_multiply():
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0
'''


def test_coverage_analysis():
    """Test the coverage analysis endpoint"""
    print("Testing coverage analysis...")

    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write Python code file
        code_file = os.path.join(tmpdir, "calculator.py")
        with open(code_file, 'w') as f:
            f.write(PYTHON_CODE)

        # Write test file
        test_file = os.path.join(tmpdir, "test_calculator.py")
        with open(test_file, 'w') as f:
            f.write(TEST_CODE)

        # Prepare files for upload
        files = {
            'files': [
                ('files', open(code_file, 'rb')),
                ('files', open(test_file, 'rb'))
            ],
            'language': (None, 'python'),
            'framework': (None, 'pytest'),
            'include_suggestions': (None, 'true')
        }

        try:
            # Call the API
            response = requests.post(f"{API_BASE}/coverage/analyze", files=files)

            # Check response
            if response.status_code == 200:
                result = response.json()
                print("✓ Coverage analysis successful!")
                print(f"  Overall coverage: {result['overall_coverage']:.1f}%")
                print(f"  Total files: {result['total_files']}")
                print(f"  Test files: {result['test_files']}")
                print(f"  Uncovered functions: {len(result['uncovered_functions'])}")

                # Check uncovered functions
                uncovered = result['uncovered_functions']
                expected_uncovered = ['fibonacci', 'is_prime', 'calculate']

                if len(uncovered) > 0:
                    print("\n  Uncovered functions:")
                    for func in uncovered[:5]:  # Show first 5
                        print(f"    - {func['name']} (priority: {func['priority']}, complexity: {func['complexity']})")

                # Test generation
                if uncovered:
                    print("\nTesting test generation...")
                    gen_response = requests.post(
                        f"{API_BASE}/coverage/generate-tests",
                        json={
                            "uncovered_functions": uncovered[:2],  # Generate for first 2 functions
                            "project_context": "Simple calculator application"
                        }
                    )

                    if gen_response.status_code == 200:
                        gen_result = gen_response.json()
                        print("✓ Test generation successful!")
                        print(f"  Generated {len(gen_result['generated_tests'])} test(s)")
                        print(f"  Coverage improvement: {gen_result['coverage_improvement']:.1f}%")
                    else:
                        print("✗ Test generation failed:", gen_response.status_code)

                return True
            else:
                print("✗ Coverage analysis failed:", response.status_code)
                print(response.text)
                return False

        except Exception as e:
            print(f"✗ Error during testing: {e}")
            return False


def test_supported_languages():
    """Test getting supported languages"""
    print("\nTesting supported languages endpoint...")

    try:
        response = requests.get(f"{API_BASE}/coverage/supported-languages")

        if response.status_code == 200:
            languages = response.json()
            print("✓ Supported languages retrieved successfully!")
            print(f"  Languages: {', '.join([lang['name'] for lang in languages['languages']])}")
            return True
        else:
            print("✗ Failed to get supported languages:", response.status_code)
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("Starting Code Coverage Feature Tests\n")
    print("=" * 50)

    # Check if server is running
    try:
        response = requests.get(f"{API_BASE.replace('/api/v1', '')}/health")
        if response.status_code != 200:
            print("✗ Server is not running. Please start the backend server first.")
            return
    except:
        print("✗ Cannot connect to server. Please start the backend server first.")
        print("  Run: cd src/backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001")
        return

    print("✓ Server is running\n")

    # Run tests
    test_results = []
    test_results.append(test_supported_languages())
    test_results.append(test_coverage_analysis())

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(test_results)
    total = len(test_results)
    print(f"  Passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed! The code coverage feature is working correctly.")
    else:
        print("✗ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()