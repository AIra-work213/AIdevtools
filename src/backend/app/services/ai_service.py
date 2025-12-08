import json
import time
from typing import Any, Dict, List, Optional, Union
import structlog

from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import LoggerMixin

logger = structlog.get_logger(__name__)


class SchemaGuidedPrompt:
    """Schema-guided reasoning prompt template for structured output"""

    TEST_GENERATION_SCHEMA = {
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
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "feature": {"type": "string"},
                    "story": {"type": "string"},
                    "test_type": {"type": "string"},
                    "complexity": {"type": "string", "enum": ["simple", "medium", "complex"]}
                }
            }
        },
        "required": ["test_cases"]
    }

    API_TEST_SCHEMA = {
        "type": "object",
        "properties": {
            "endpoints": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "method": {"type": "string"},
                        "test_scenarios": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string", "enum": ["happy_path", "negative", "edge_case"]},
                                    "description": {"type": "string"},
                                    "request_data": {"type": "object"},
                                    "expected_response": {"type": "object"},
                                    "expected_status": {"type": "integer"}
                                },
                                "required": ["name", "type", "expected_status"]
                            }
                        }
                    },
                    "required": ["path", "method", "test_scenarios"]
                }
            }
        },
        "required": ["endpoints"]
    }

    @staticmethod
    def build_prompt_with_schema(system_prompt: str, user_prompt: str, schema: Dict[str, Any]) -> str:
        """Build prompt with schema guidance for structured output"""
        return f"""
{system_prompt}

CRITICAL: Your response MUST follow this exact JSON schema:
```json
{json.dumps(schema, indent=2)}
```

Your entire response should be valid JSON that conforms to this schema.
Do not include any text outside the JSON structure.

User Request:
{user_prompt}

Provide your response:
"""


class CloudEvolutionClient:
    """Client for Cloud.ru Evolution API with schema-guided reasoning"""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.CLOUD_API_KEY,
            base_url=settings.CLOUD_API_URL
        )
        self.model = settings.CLOUD_MODEL
        self.logger = logger.bind(service="CloudEvolutionClient")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = None,
        temperature: float = None,
        response_schema: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """Send chat completion request with optional schema guidance"""
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or settings.MAX_TOKENS_GENERATION,
                "temperature": temperature or settings.TEMPERATURE_GENERATION,
                "presence_penalty": 0,
                "top_p": settings.TOP_P_GENERATION
            }

            if response_schema:
                # Modify the last message to include schema guidance
                schema_guided_message = messages[-1].copy()
                schema_guided_message["content"] = SchemaGuidedPrompt.build_prompt_with_schema(
                    messages[0]["content"] if messages else "",
                    messages[-1]["content"],
                    response_schema
                )
                messages[-1] = schema_guided_message

            response = await self.client.chat.completions.create(**params)
            content = response.choices[0].message.content

            # Parse JSON if schema was provided
            if response_schema:
                try:
                    # Extract JSON from response (in case there's extra text)
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start != -1 and end != 0:
                        json_content = content[start:end]
                        return json.loads(json_content)
                    else:
                        self.logger.warning("No JSON found in schema-guided response")
                        return content
                except json.JSONDecodeError as e:
                    self.logger.error("Failed to parse JSON response", error=str(e))
                    # Fallback to raw content
                    return content

            return content

        except Exception as e:
            self.logger.error("Cloud API request failed", error=str(e))
            raise


class AIService(LoggerMixin):
    """AI service for test generation and analysis"""

    def __init__(self):
        self.llm_client = CloudEvolutionClient()
        self._logger = logger.bind(service="AIService")

    async def generate_manual_tests(
        self,
        requirements: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate manual tests from requirements using schema-guided reasoning"""
        start_time = time.time()

        system_prompt = """
        You are an expert QA engineer with 10+ years of experience in test automation.
        Analyze the user requirements and generate comprehensive test cases.

        Guidelines:
        1. Extract all functional requirements from the input
        2. Create test cases for positive scenarios
        3. Consider edge cases and error conditions
        4. Follow the AAA pattern (Arrange-Act-Assert)
        5. Use clear, descriptive test names
        6. Include expected results for each test

        Focus on:
        - User workflows and interactions
        - Business rules and validations
        - Error handling
        - Edge cases and boundary values
        """

        user_prompt = f"""
        Generate manual test cases for the following requirements:

        Requirements:
        {requirements}

        {f'Additional Metadata: {metadata}' if metadata else ''}

        Generate comprehensive test cases that cover all aspects of the requirements.
        """

        try:
            # Use schema-guided reasoning for structured output
            result = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_schema=SchemaGuidedPrompt.TEST_GENERATION_SCHEMA
            )

            # Generate Python code from structured result
            if isinstance(result, dict):
                code = await self._generate_python_code_from_structure(result, metadata)
            else:
                # Fallback: generate code directly
                code = await self._generate_code_directly(requirements, metadata)
                result = {"test_cases": []}

            generation_time = time.time() - start_time

            return {
                "code": code,
                "test_cases": result.get("test_cases", []),
                "generation_time": generation_time,
                "metadata": metadata
            }

        except Exception as e:
            self.logger.error("Failed to generate manual tests", error=str(e))
            raise

    async def generate_api_tests(
        self,
        openapi_spec: str,
        endpoint_filter: Optional[List[str]] = None,
        test_types: List[str] = None
    ) -> Dict[str, Any]:
        """Generate API tests from OpenAPI specification"""
        start_time = time.time()

        system_prompt = """
        You are an expert API testing engineer.
        Analyze the OpenAPI specification and generate comprehensive API tests.

        Guidelines:
        1. Generate tests for all HTTP methods
        2. Include positive (happy path) test cases
        3. Include negative test cases (invalid data, missing fields)
        4. Test edge cases and boundary values
        5. Include authentication/authorization tests
        6. Validate response status codes and schemas
        """

        user_prompt = f"""
        Generate API tests for the following OpenAPI specification:

        ```yaml
        {openapi_spec}
        ```

        {f'Endpoints to focus on: {endpoint_filter}' if endpoint_filter else ''}

        {f'Test types to generate: {test_types}' if test_types else ''}

        Generate comprehensive test cases covering all specified endpoints.
        """

        try:
            # Parse OpenAPI first for context
            parsed_spec = await self._parse_openapi_spec(openapi_spec)

            # Use schema-guided reasoning
            result = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_schema=SchemaGuidedPrompt.API_TEST_SCHEMA
            )

            # Generate Python code
            if isinstance(result, dict):
                code = await self._generate_api_code_from_structure(result, parsed_spec)
            else:
                code = await self._generate_api_code_directly(openapi_spec)
                result = {"endpoints": []}

            generation_time = time.time() - start_time

            return {
                "code": code,
                "endpoints_covered": [ep.get("path") for ep in result.get("endpoints", [])],
                "test_matrix": self._build_test_matrix(result),
                "generation_time": generation_time
            }

        except Exception as e:
            self.logger.error("Failed to generate API tests", error=str(e))
            raise

    async def validate_code(
        self,
        code: str,
        standards: List[str] = None
    ) -> Dict[str, Any]:
        """Validate Python code against testing standards"""
        validation_prompt = f"""
        Analyze the following Python test code and validate it against testing standards:

        Code:
        ```python
        {code}
        ```

        Standards to check:
        {', '.join(standards or ['allure'])}

        Provide:
        1. Syntax validation
        2. Structure validation
        3. Best practices check
        4. Specific standards compliance
        5. Suggestions for improvement
        """

        try:
            response = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a Python code review expert specializing in test automation."},
                    {"role": "user", "content": validation_prompt}
                ]
            )

            # Parse validation results
            return self._parse_validation_response(response)

        except Exception as e:
            self.logger.error("Code validation failed", error=str(e))
            raise

    async def _generate_python_code_from_structure(
        self,
        structured_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate Python code from structured test cases"""
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
        for test_case in structured_result.get("test_cases", []):
            method_code = f"""
    @allure.title("{test_case['title']}")
    @allure.severity(Severity.{test_case['priority'].upper()})
    @allure.manual
    def test_{self._to_snake_case(test_case['title'])}(self):
        \"\"\"
        {test_case.get('description', '')}
        \"\"\"
        {self._generate_test_steps(test_case['steps'], test_case['expected_result'])}
"""
            test_methods.append(method_code)

        return code_template.format(
            feature=metadata.get("feature", "Default Feature") if metadata else "Default Feature",
            story=metadata.get("story", "Default Story") if metadata else "Default Story",
            owner_decorator=f'@allure.label("owner", "{metadata.get("owner", "QA")}")' if metadata else "",
            class_name="GeneratedTests",
            test_methods="".join(test_methods)
        )

    async def _generate_api_code_from_structure(
        self,
        structured_result: Dict[str, Any],
        parsed_spec: Dict[str, Any]
    ) -> str:
        """Generate API test code from structured result"""
        # Implementation for API code generation
        pass

    async def _parse_openapi_spec(self, spec: str) -> Dict[str, Any]:
        """Parse OpenAPI specification"""
        # Implementation for OpenAPI parsing
        return {"parsed": True}

    def _build_test_matrix(self, result: Dict[str, Any]) -> Dict[str, List[str]]:
        """Build test matrix from structured result"""
        matrix = {}
        for endpoint in result.get("endpoints", []):
            path = endpoint.get("path")
            scenarios = endpoint.get("test_scenarios", [])
            matrix[path] = [s.get("name") for s in scenarios]
        return matrix

    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse validation response from AI"""
        # Implementation for parsing validation response
        return {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return re.sub(r'\W+', '_', s2).lower('_')

    def _generate_test_steps(self, steps: List[str], expected: str) -> str:
        """Generate test steps with allure.step"""
        step_code = []
        for i, step in enumerate(steps):
            step_code.append(f'        with allure.step("Step {i+1}: {step}"):')
            step_code.append('            # TODO: Implement step')
            step_code.append('            pass')

        step_code.append(f'        with allure.step("Assert: {expected}"):')
        step_code.append('            # TODO: Add assertions')
        step_code.append('            pass')

        return '\n'.join(step_code)