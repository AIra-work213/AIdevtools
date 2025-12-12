#!/usr/bin/env python3
"""
Generate UI test for python.org using the AI service
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/backend'))

from app.services.ai_service import AIService
from app.services.code_validator import CodeValidator


async def generate_python_org_test():
    """Generate a Selenium test for python.org"""
    print("=" * 60)
    print("Generating Selenium UI Test for python.org")
    print("=" * 60)

    # Initialize services
    ai_service = AIService()
    validator = CodeValidator(timeout=60)

    try:
        print("\n[Step 1] Analyzing python.org website structure...")

        # Generate the test using AI service
        print("\n[Step 2] Generating Selenium test with Allure reporting...")
        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://www.python.org",
            framework="selenium"
        )

        if not result or "code" not in result:
            print("ERROR: Failed to generate test code")
            return False

        code = result["code"]
        print(f"\n✓ Test generated successfully (length: {len(code)} characters)")

        # Save the generated test
        output_file = "generated_python_org_test.py"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"✓ Test saved to: {output_file}")

        # Show the generated code
        print("\n" + "=" * 60)
        print("GENERATED TEST CODE:")
        print("=" * 60)
        print(code[:2000] + "..." if len(code) > 2000 else code)
        print("=" * 60)

        # Validate syntax
        print("\n[Step 3] Validating syntax...")
        syntax_errors = validator.validate_syntax(code)

        if syntax_errors:
            print(f"✗ Syntax errors found: {len(syntax_errors)}")
            for error in syntax_errors[:3]:
                print(f"  - {error}")
            return False
        else:
            print("✓ Syntax validation passed")

        # Execute the test
        print("\n[Step 4] Executing the generated test...")
        execution = validator.execute_code(
            code=code,
            run_with_pytest=True
        )

        print(f"\nExecution Results:")
        print(f"  - Can execute: {execution.can_execute}")
        print(f"  - Runtime errors: {len(execution.runtime_errors)}")

        if execution.runtime_errors:
            print("\nRuntime errors:")
            for error in execution.runtime_errors[:5]:
                print(f"  - {error[:200]}")

        # Check Allure results
        if execution.allure_results:
            results = execution.allure_results
            print(f"\nTest Results Summary:")
            print(f"  - Total tests: {results.get('total_tests', 0)}")
            print(f"  - Passed: {results.get('passed', 0)}")
            print(f"  - Failed: {results.get('failed', 0)}")
            print(f"  - Broken: {results.get('broken', 0)}")
            print(f"  - Skipped: {results.get('skipped', 0)}")

            # Check if we have successful tests
            if results.get('passed', 0) > 0:
                print("\n✓ SUCCESS: Tests passed!")
                return True
            else:
                print("\n✗ FAILURE: No tests passed")
                return False
        else:
            print("\n⚠ No Allure results available")

            # Check if execution was successful even without Allure
            if execution.can_execute and not execution.runtime_errors:
                print("✓ Test code executed successfully (no runtime errors)")
                return True
            else:
                print("✗ Test execution failed")
                return False

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""
    success = await generate_python_org_test()

    if success:
        print("\n" + "=" * 60)
        print("✓ TEST GENERATION AND EXECUTION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ TEST GENERATION OR EXECUTION FAILED")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())