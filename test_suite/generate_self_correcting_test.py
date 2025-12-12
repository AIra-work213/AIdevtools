#!/usr/bin/env python3
"""
Generate UI test for python.org with self-correction capability
"""
import asyncio
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/backend'))

from app.services.ai_service import AIService
from app.services.code_validator import CodeValidator


async def generate_and_correct_test():
    """Generate and iteratively correct a Selenium test for python.org"""
    print("=" * 60)
    print("Generating Self-Correcting Selenium UI Test for python.org")
    print("=" * 60)

    # Initialize services
    ai_service = AIService()
    validator = CodeValidator(timeout=60)

    best_code = None
    best_results = None
    max_attempts = 3

    for attempt in range(max_attempts):
        print(f"\n{'='*60}")
        print(f"ATTEMPT {attempt + 1} / {max_attempts}")
        print(f"{'='*60}")

        if attempt == 0:
            # First attempt - generate fresh test
            print("\n[Step 1] Generating initial Selenium test...")
            result = await ai_service.generate_ui_tests(
                input_method="url",
                url="https://www.python.org",
                framework="selenium",
                custom_prompt="""Generate a comprehensive but robust Selenium test for python.org with:
- Focus on tests that actually work in headless mode
- Test main functionality: navigation, search, page titles
- Use flexible selectors and assertions
- Don't test too many pages - focus on core functionality
- Include proper error handling and waits"""
            )
        else:
            # Subsequent attempts - fix based on previous errors
            print("\n[Step 1] Fixing test based on previous errors...")

            # Prepare error context
            error_context = f"""
Previous attempt failed with these issues:
- Total tests: {best_results.get('total_tests', 0)}
- Passed: {best_results.get('passed', 0)}
- Failed: {best_results.get('failed', 0)}
- Broken: {best_results.get('broken', 0)}

Common issues:
1. Chrome driver initialization failures
2. Elements not found on certain pages
3. URL assertion failures

Please fix the test code to address these issues. Make it more robust and flexible.
Focus on ensuring the tests actually run and pass.
"""

            # Use the AI service to fix the code
            from app.services.cloud_evolution_client import CloudEvolutionClient
            client = CloudEvolutionClient()

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert in Selenium test automation. Your task is to fix a failing Selenium test to make it robust and working."
                },
                {
                    "role": "user",
                    "content": f"""Please fix this Selenium test for python.org to make it work correctly:

Current test code:
{best_code}

{error_context}

Please return the complete fixed test code. Make sure:
1. Chrome options include all necessary arguments for headless mode
2. Test assertions are flexible and robust
3. Elements are properly waited for
4. Error handling is included
5. Tests can actually run in a headless Linux environment"""
                }
            ]

            response = await client.complete(
                messages=messages,
                max_tokens=4000,
                temperature=0.2
            )

            result = {
                "code": response.content
            }

        if not result or "code" not in result:
            print("ERROR: Failed to generate test code")
            continue

        code = result["code"]
        print(f"\n✓ Test generated (length: {len(code)} characters)")

        # Save the generated test
        output_file = f"generated_test_attempt_{attempt + 1}.py"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"✓ Test saved to: {output_file}")

        # Execute and validate the test
        print("\n[Step 2] Executing test...")
        execution = validator.execute_code(
            code=code,
            run_with_pytest=True
        )

        print(f"\nExecution Results:")
        print(f"  - Can execute: {execution.can_execute}")
        print(f"  - Runtime errors: {len(execution.runtime_errors)}")

        if execution.allure_results:
            results = execution.allure_results
            print(f"\nTest Results Summary:")
            print(f"  - Total tests: {results.get('total_tests', 0)}")
            print(f"  - Passed: {results.get('passed', 0)}")
            print(f"  - Failed: {results.get('failed', 0)}")
            print(f"  - Broken: {results.get('broken', 0)}")
            print(f"  - Skipped: {results.get('skipped', 0)}")

            # Check if this is the best result so far
            if best_results is None or results.get('passed', 0) > best_results.get('passed', 0):
                best_code = code
                best_results = results
                print("\n✓ This is the best result so far!")

                # If all tests pass, we're done
                if results.get('passed', 0) == results.get('total_tests', 0):
                    print("\n✅ All tests passed! Test generation complete.")
                    break
            elif best_results is None:
                # First attempt, even if no Allure results
                best_code = code
                best_results = {'total_tests': 0, 'passed': 0, 'failed': 0, 'broken': 0}

        # If there are runtime errors, show them
        if execution.runtime_errors:
            print("\nRuntime errors:")
            for error in execution.runtime_errors[:3]:
                print(f"  - {error[:200]}")

        # Prepare for next iteration if needed
        if attempt < max_attempts - 1:
            print("\n⏳ Preparing for correction attempt...")
            await asyncio.sleep(2)  # Brief pause between attempts

    # Save the best version
    if best_code:
        with open("best_python_org_test.py", "w", encoding="utf-8") as f:
            f.write(best_code)
        print(f"\n✓ Best test saved to: best_python_org_test.py")

        # Final summary
        print("\n" + "=" * 60)
        print("FINAL RESULTS:")
        print(f"  - Total tests: {best_results.get('total_tests', 0)}")
        print(f"  - Passed: {best_results.get('passed', 0)}")
        print(f"  - Failed: {best_results.get('failed', 0)}")
        print(f"  - Broken: {best_results.get('broken', 0)}")
        print("=" * 60)

        return best_results.get('passed', 0) > 0
    else:
        print("\n✗ No successful test generated")
        return False


async def main():
    """Main function"""
    success = await generate_and_correct_test()

    if success:
        print("\n" + "=" * 60)
        print("✓ TEST GENERATION WITH SELF-CORRECTION COMPLETED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ TEST GENERATION FAILED")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())