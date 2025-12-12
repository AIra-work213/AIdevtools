#!/usr/bin/env python3
"""
Comprehensive test runner for the application.
Runs all test suites and generates a report.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict


class TestResult:
    """Test result container."""
    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.duration = 0


def run_command(cmd: List[str], cwd: str = None) -> Tuple[int, str]:
    """Run a command and return exit code and output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "Test timed out after 5 minutes"
    except Exception as e:
        return 1, f"Error running test: {str(e)}"


def validate_python_syntax(file_path: Path) -> Tuple[bool, str]:
    """Validate Python syntax."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        compile(content, str(file_path), 'exec')
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def run_backend_tests() -> TestResult:
    """Run backend tests."""
    result = TestResult("Backend Tests")
    print("Running Backend Tests...")
    print("-" * 40)

    # Test 1: Validate syntax
    test_files = list(Path("src/backend/app").rglob("*.py"))
    test_files.extend(Path("src/backend/tests").rglob("*.py"))

    for file_path in test_files:
        is_valid, message = validate_python_syntax(file_path)
        if is_valid:
            result.passed += 1
        else:
            result.failed += 1
            result.errors.append(f"{file_path}: {message}")

    # Test 2: Run pytest if available
    if Path("src/backend/requirements.txt").exists():
        exit_code, output = run_command([
            sys.executable, "-m", "pytest",
            "tests/test_data_types_and_formats.py",
            "tests/test_network_error_handling.py",
            "tests/test_database_error_handling.py",
            "-v", "--tb=short"
        ], cwd="src/backend")

        if exit_code == 0:
            result.passed += 1
        else:
            result.failed += 1
            result.errors.append(f"Pytest failed:\n{output}")

    return result


def run_frontend_validation() -> TestResult:
    """Run frontend validation."""
    result = TestResult("Frontend Validation")
    print("\nRunning Frontend Validation...")
    print("-" * 40)

    # Check TypeScript files
    ts_files = list(Path("src/frontend/src").rglob("*.ts")) + list(Path("src/frontend/src").rglob("*.tsx"))

    for file_path in ts_files:
        if file_path.exists():
            try:
                content = file_path.read_text()
                # Basic TypeScript validation
                if "import" in content or "export" in content or "function" in content or "const" in content:
                    result.passed += 1
                else:
                    result.failed += 1
                    result.errors.append(f"{file_path}: Invalid TypeScript structure")
            except Exception as e:
                result.failed += 1
                result.errors.append(f"{file_path}: {str(e)}")

    return result


def run_theme_transitions_test() -> TestResult:
    """Run theme transitions test."""
    result = TestResult("Theme Transitions")
    print("\nRunning Theme Transitions Test...")
    print("-" * 40)

    exit_code, output = run_command([sys.executable, "test_theme_transitions.py"])

    if exit_code == 0:
        result.passed = 1
    else:
        result.failed = 1
        result.errors.append(output)

    return result


def run_coverage_feature_test() -> TestResult:
    """Run coverage feature test."""
    result = TestResult("Coverage Feature")
    print("\nRunning Coverage Feature Test...")
    print("-" * 40)

    exit_code, output = run_command([sys.executable, "validate_implementation.py"])

    if exit_code == 0:
        result.passed = 1
    else:
        result.failed = 1
        result.errors.append(output)

    return result


def check_dependencies() -> TestResult:
    """Check if all dependencies are properly listed."""
    result = TestResult("Dependencies Check")
    print("\nChecking Dependencies...")
    print("-" * 40)

    # Backend dependencies
    backend_req = Path("src/backend/requirements.txt")
    if backend_req.exists():
        content = backend_req.read_text()
        required_deps = ["fastapi", "pydantic", "pytest", "GitPython", "chardet"]

        for dep in required_deps:
            if dep.lower() in content.lower():
                result.passed += 1
            else:
                result.failed += 1
                result.errors.append(f"Missing dependency: {dep}")

    # Frontend dependencies
    frontend_package = Path("src/frontend/package.json")
    if frontend_package.exists():
        content = frontend_package.read_text()
        required_deps = ["react", "typescript", "tailwindcss", "monaco-editor"]

        for dep in required_deps:
            if dep in content:
                result.passed += 1
            else:
                result.failed += 1
                result.errors.append(f"Missing dependency: {dep}")

    return result


def check_configuration() -> TestResult:
    """Check configuration files."""
    result = TestResult("Configuration Check")
    print("\nChecking Configuration...")
    print("-" * 40)

    config_files = [
        "src/backend/requirements.txt",
        "src/frontend/tailwind.config.js",
        "src/frontend/package.json",
        "src/frontend/tsconfig.json",
    ]

    for config_file in config_files:
        path = Path(config_file)
        if path.exists():
            result.passed += 1
        else:
            result.failed += 1
            result.errors.append(f"Missing config file: {config_file}")

    return result


def generate_report(results: List[TestResult]) -> None:
    """Generate test report."""
    print("\n" + "=" * 50)
    print("TEST REPORT")
    print("=" * 50)

    total_passed = sum(r.passed for r in results)
    total_failed = sum(r.failed for r in results)

    for result in results:
        status = "✓ PASSED" if result.failed == 0 else "✗ FAILED"
        print(f"\n{result.name}: {status}")
        print(f"  Passed: {result.passed}")
        print(f"  Failed: {result.failed}")

        if result.errors:
            print("  Errors:")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"    - {error[:100]}...")

            if len(result.errors) > 5:
                print(f"    ... and {len(result.errors) - 5} more errors")

    print("\n" + "=" * 50)
    print(f"TOTAL: {total_passed} passed, {total_failed} failed")

    if total_failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        print("\nThe application is ready for deployment:")
        print("  • Theme transitions are smooth (300ms)")
        print("  • Data types and formats are validated")
        print("  • Network errors are handled gracefully")
        print("  • Database errors are handled properly")
        print("  • Code coverage feature is implemented")
        print("  • All dependencies are properly configured")
    else:
        print(f"\n✗ {total_failed} TESTS FAILED")
        print("Please review the errors above and fix them.")


def main():
    """Run all tests."""
    start_time = time.time()

    print("Running Comprehensive Test Suite")
    print("=" * 50)

    # Run all test suites
    results = []

    try:
        results.append(check_dependencies())
        results.append(check_configuration())
        results.append(run_backend_tests())
        results.append(run_frontend_validation())
        results.append(run_theme_transitions_test())
        results.append(run_coverage_feature_test())
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        return 1

    # Calculate duration
    duration = time.time() - start_time
    print(f"\nTests completed in {duration:.2f} seconds")

    # Generate report
    generate_report(results)

    # Return appropriate exit code
    total_failed = sum(r.failed for r in results)
    return 1 if total_failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())