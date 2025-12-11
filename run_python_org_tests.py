#!/usr/bin/env python3
"""
Run Python.org UI tests with increased timeout settings
"""
import os
import sys
import subprocess

def run_tests():
    """Run the python.org UI tests with proper timeout settings"""

    # Set environment variables for longer timeouts
    env = os.environ.copy()
    env['PYTEST_CURRENT_TEST'] = ''
    env['PYTEST_TIMEOUT'] = '300'  # 5 minutes per test

    # Run pytest with increased timeout
    cmd = [
        'python', '-m', 'pytest',
        'generated_test_attempt_1.py',
        '-v',
        '--tb=short',
        '--timeout=300',  # 5 minutes timeout per test
        '--timeout-method=thread',
        '--alluredir=allure-results-python-org-final',
        '-x'  # Stop on first failure to see issues
    ]

    print("Running Python.org UI tests with extended timeouts...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes total
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)

        print(f"\nReturn code: {result.returncode}")

        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed")

    except subprocess.TimeoutExpired:
        print("\n⏰ Test execution timed out after 30 minutes")
    except KeyboardInterrupt:
        print("\n⚠ Test execution interrupted")
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")

if __name__ == "__main__":
    # Install pytest-timeout if not present
    subprocess.run([
        sys.executable, '-m', 'pip', 'install', 'pytest-timeout'
    ], capture_output=True)

    run_tests()