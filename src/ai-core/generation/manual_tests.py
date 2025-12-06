import re
from typing import Dict, List, Any, Optional
import structlog
from ..llm.client import CloudEvolutionClient

logger = structlog.get_logger(__name__)


class ManualTestGenerator:
    """Generator for manual test cases from requirements"""

    def __init__(self, llm_client: CloudEvolutionClient):
        self.llm = llm_client
        self.logger = logger.bind(generator="ManualTestGenerator")

    async def generate(
        self,
        requirements: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate manual tests from requirements
        """
        start_time = time.time()

        # Extract test cases using AI
        test_cases = await self._extract_test_cases(requirements)

        # Generate Python code with Allure decorators
        code = await self._generate_python_code(test_cases, metadata)

        # Validate generated code
        validation = await self._validate_code(code)

        generation_time = time.time() - start_time

        return {
            "code": code,
            "test_cases": test_cases,
            "validation": validation,
            "generation_time": generation_time,
            "metadata": metadata
        }

    async def _extract_test_cases(self, requirements: str) -> List[Dict[str, Any]]:
        """Extract individual test cases from requirements"""

        schema = {
            "type": "object",
            "properties": {
                "test_cases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "steps": {"type": "array", "items": {"type": "string"}},
                            "expected_result": {"type": "string"},
                            "priority": {"type": "string", "enum": ["low", "normal", "high", "critical"]},
                            "tags": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["title", "steps", "expected_result", "priority"]
                    }
                }
            },
            "required": ["test_cases"]
        }

        system_prompt = """
        You are an expert QA engineer with 10+ years of experience in test case design.
        Analyze the user requirements and extract comprehensive test cases.

        Guidelines:
        1. Break down complex requirements into individual testable scenarios
        2. Consider both positive and negative scenarios
        3. Include edge cases and boundary conditions
        4. Focus on user workflows and business rules
        5. Ensure test cases are independent and atomic
        """

        try:
            result = await self.llm.generate_with_schema(
                prompt=requirements,
                schema=schema,
                system_prompt=system_prompt
            )

            return result.get("test_cases", [])

        except Exception as e:
            self.logger.error("Failed to extract test cases", error=str(e))
            # Fallback: create basic test case
            return [{
                "title": "Basic test case",
                "description": "Generated from requirements",
                "steps": ["Step 1", "Step 2", "Step 3"],
                "expected_result": "Expected behavior",
                "priority": "normal",
                "tags": ["generated"]
            }]

    async def _generate_python_code(
        self,
        test_cases: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Generate Python code with Allure decorators"""

        code_template = """
import allure
import pytest
from allure_commons.types import Severity

@allure.feature("{feature}")
@allure.story("{story}")
{owner_decorator}
@allure.tag("generated_by_ai")
class Test{class_name}:
{test_methods}
"""

        test_methods = []
        for i, test_case in enumerate(test_cases):
            method_name = self._to_snake_case(test_case.get("title", f"test_case_{i}"))
            if not method_name.startswith("test_"):
                method_name = f"test_{method_name}"

            severity = test_case.get("priority", "normal").upper()
            if severity not in ["LOW", "NORMAL", "HIGH", "CRITICAL"]:
                severity = "NORMAL"

            method_code = f'''    @allure.title("{test_case.get('title', 'Test Case')}")
    @allure.severity(Severity.{severity})
    @allure.manual
    def {method_name}(self):
        """
        {test_case.get('description', '')}
        """
        {self._generate_test_steps(test_case.get('steps', []), test_case.get('expected_result', ''))}'''

            test_methods.append(method_code)

        return code_template.format(
            feature=metadata.get("feature", "Generated Tests") if metadata else "Generated Tests",
            story=metadata.get("story", "AI Generated") if metadata else "AI Generated",
            owner_decorator=f'@allure.label("owner", "{metadata.get("owner", "QA")}")' if metadata else '@allure.label("owner", "QA")',
            class_name="GeneratedTests",
            test_methods="\n".join(test_methods)
        )

    def _generate_test_steps(self, steps: List[str], expected: str) -> str:
        """Generate test steps with allure.step"""
        step_code = []
        for i, step in enumerate(steps, 1):
            # Clean up step text
            clean_step = step.strip().replace('"', "'")
            if not clean_step:
                clean_step = f"Step {i}"

            step_code.append(f'        with allure.step("Step {i}: {clean_step}"):')
            step_code.append('            # TODO: Implement test step')
            step_code.append('            pass')

        step_code.append(f'        with allure.step("Assert: {expected}"):')
        step_code.append('            # TODO: Add assertions')
        step_code.append('            pass')

        return '\n'.join(step_code)

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        # Remove non-alphanumeric characters and convert to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Replace spaces and other non-alphanumeric with underscores
        s3 = re.sub(r'\W+', '_', s2)
        # Remove multiple underscores and convert to lowercase
        return re.sub(r'_+', '_', s3).lower('_')

    async def _validate_code(self, code: str) -> Dict[str, Any]:
        """Validate the generated Python code"""
        try:
            # Syntax check
            compile(code, '<string>', 'exec')
            is_valid = True
            errors = []
        except SyntaxError as e:
            is_valid = False
            errors = [{
                "type": "SyntaxError",
                "message": e.msg,
                "line": e.lineno,
                "column": e.offset
            }]

        # Basic structure validation
        warnings = []
        if "@allure.feature" not in code:
            warnings.append({
                "type": "missing_decorator",
                "message": "Missing @allure.feature decorator"
            })

        if "@allure.story" not in code:
            warnings.append({
                "type": "missing_decorator",
                "message": "Missing @allure.story decorator"
            })

        # Count test functions
        test_count = len(re.findall(r'def test_\w+\(', code))
        if test_count == 0:
            warnings.append({
                "type": "no_tests",
                "message": "No test functions found"
            })

        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "metrics": {
                "test_functions": test_count,
                "lines_of_code": len(code.splitlines()),
                "allure_decorators": code.count("@allure.")
            }
        }


# Import time for timing
import time