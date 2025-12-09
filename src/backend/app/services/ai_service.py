import json
import time
from typing import Any, Dict, List, Optional, Union
import structlog

from openai import AsyncOpenAI
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
        self.client = AsyncOpenAI(
            api_key=settings.CLOUD_API_KEY,
            base_url=settings.CLOUD_API_URL,
            timeout=120.0,  # 2 minutes timeout for each request
            max_retries=2   # Reduce retries from 5 to 2 for faster failure
        )
        self.model = settings.CLOUD_MODEL
        self.logger = logger.bind(service="CloudEvolutionClient")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = None,
        temperature: float = None,
        response_schema: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        max_retries: int = 3
    ) -> Union[str, Dict[str, Any]]:
        """Send chat completion request with optional schema guidance and automatic retry on invalid responses"""
        
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
        
        # Retry loop for handling invalid responses
        for attempt in range(max_retries):
            try:
                # Log request details
                self.logger.info(
                    "Sending request to Cloud API",
                    model=self.model,
                    messages_count=len(messages),
                    max_tokens=params["max_tokens"],
                    temperature=params["temperature"],
                    has_schema=response_schema is not None,
                    attempt=attempt + 1,
                    max_attempts=max_retries
                )

                response = await self.client.chat.completions.create(**params)
                
                # Check if response has choices
                if not response.choices:
                    self.logger.error("Cloud API returned empty choices", attempt=attempt + 1)
                    raise ValueError("Empty response from Cloud API")
                
                content = response.choices[0].message.content
                
                # Log successful response with content preview
                self.logger.info(
                    "Cloud API response received",
                    finish_reason=response.choices[0].finish_reason,
                    usage_prompt_tokens=response.usage.prompt_tokens if response.usage else None,
                    usage_completion_tokens=response.usage.completion_tokens if response.usage else None,
                    content_length=len(content) if content else 0,
                    content_preview=(content[:100] if content else "EMPTY"),
                    attempt=attempt + 1
                )
                
                # Validate content is not empty
                if not content or not content.strip():
                    self.logger.error("Cloud API returned empty content", attempt=attempt + 1)
                    raise ValueError("Empty content from Cloud API")

                # Parse JSON if schema was provided
                if response_schema:
                    try:
                        # Extract JSON from response (in case there's extra text)
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        if start != -1 and end != 0:
                            json_content = content[start:end]
                            parsed_json = json.loads(json_content)
                            self.logger.info("Successfully parsed JSON response", attempt=attempt + 1)
                            return parsed_json
                        else:
                            self.logger.warning("No JSON found in schema-guided response", attempt=attempt + 1)
                            if attempt < max_retries - 1:
                                self.logger.info("Retrying due to invalid JSON format")
                                continue
                            return content
                    except json.JSONDecodeError as e:
                        self.logger.error(
                            "Failed to parse JSON response", 
                            error=str(e), 
                            content_sample=content[:200],
                            attempt=attempt + 1
                        )
                        if attempt < max_retries - 1:
                            self.logger.info("Retrying due to JSON parse error")
                            continue
                        # Last attempt - fallback to raw content
                        return content

                # Success - return content
                return content

            except ValueError as e:
                # Empty response errors - retry
                if attempt < max_retries - 1:
                    self.logger.warning(
                        "Retrying due to empty response",
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    continue
                else:
                    # Last attempt failed
                    self.logger.error("All retry attempts exhausted for empty response")
                    raise
                    
            except Exception as e:
                # Enhanced error logging with more details
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "model": self.model,
                    "messages_count": len(messages) if messages else 0,
                    "attempt": attempt + 1
                }
                
                # Try to extract more details from OpenAI error
                if hasattr(e, 'response'):
                    error_details["status_code"] = getattr(e.response, 'status_code', None)
                    error_details["response_text"] = getattr(e.response, 'text', None)
                if hasattr(e, 'status_code'):
                    error_details["status_code"] = e.status_code
                if hasattr(e, 'body'):
                    error_details["error_body"] = e.body
                    
                self.logger.error("Cloud API request failed", **error_details)
                
                # Don't retry on non-retryable errors
                raise


class AIService(LoggerMixin):
    """AI service for test generation and analysis"""

    def __init__(self):
        self.llm_client = CloudEvolutionClient()
        self._logger = logger.bind(service="AIService")

    async def generate_manual_tests(
        self,
        requirements: str,
        metadata: Optional[Dict[str, Any]] = None,
        generation_settings: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate manual tests from requirements - optimized single request"""
        start_time = time.time()

        # Extract settings with defaults
        settings = generation_settings or {}
        test_type = settings.get("test_type", "manual")
        detail_level = settings.get("detail_level", "standard")
        use_aaa = settings.get("use_aaa_pattern", True)
        include_negative = settings.get("include_negative_tests", True)
        temperature = settings.get("temperature", 0.3)
        max_tokens = settings.get("max_tokens", 16000)
        language = settings.get("language", "python")
        framework = settings.get("framework", "pytest")

        # Build comprehensive prompt for direct Python code generation
        feature = metadata.get("feature", "User Generated") if metadata else "User Generated"
        owner = metadata.get("owner", "QA Engineer") if metadata else "QA Engineer"

        # Build context from conversation history
        context = ""
        if conversation_history and len(conversation_history) > 0:
            context = "\n\nPrevious conversation context:\n"
            for msg in conversation_history[-5:]:  # Use last 5 messages for context
                context += f"{msg['type'].upper()}: {msg['content']}\n"
            context += "\n"

        # Build system prompt based on settings
        system_prompt = f"""You are an expert QA engineer specializing in test automation with {framework} and Allure.
Generate ready-to-use {language} test code that follows best practices."""

        # Build detailed instructions based on settings
        instructions = []
        if detail_level == "minimal":
            instructions.append("Generate minimal tests with only essential test cases")
        elif detail_level == "detailed":
            instructions.append("Generate comprehensive tests with many edge cases and detailed documentation")
        else:  # standard
            instructions.append("Generate standard tests covering main scenarios")

        if use_aaa:
            instructions.append("Use Arrange-Act-Assert pattern in test structure")

        if include_negative:
            instructions.append("Include negative test scenarios for error handling")

        user_prompt = f"""Generate {framework} test code for these requirements:

{context}
Current requirements:
{requirements}

Instructions:
{chr(10).join(f"- {inst}" for inst in instructions)}

Generate a complete {language} test class with:
1. Import statements (allure, {framework}, allure_commons.types.Severity)
2. Class decorated with @allure.feature("{feature}") and @allure.story("Test Scenarios")
3. Multiple test methods covering:
   - Happy path scenarios
   - Edge cases
   {"   - Error conditions" if include_negative else ""}
4. Each test method should have:
   - @allure.title() with clear test name
   - @allure.severity() (NORMAL, HIGH, or CRITICAL)
   - @allure.manual decorator
   - Docstring describing the test
   - allure.step() for each test step with TODO comments
   - Assertion step at the end

Example format:
```python
import allure
import {framework}
from allure_commons.types import Severity

@allure.feature("{feature}")
@allure.story("Test Scenarios")
@allure.label("owner", "{owner}")
@allure.tag("generated_by_ai")
class TestGeneratedScenarios:

    @allure.title("Test example scenario")
    @allure.severity(Severity.NORMAL)
    @allure.manual
    def test_example_scenario(self):
        \"\"\"Test description here\"\"\"
        {"        # Arrange" if use_aaa else ""}
        {"        test_data = 'example'" if use_aaa else ""}
        {"        " if use_aaa else ""}with allure.step("Step 1: Do something"):
            # TODO: Implement step
            pass
        {"        # Act" if use_aaa else ""}
        {"        result = perform_action()" if use_aaa else ""}
        {"        " if use_aaa else ""}with allure.step("Assert: Expected result"):
            # TODO: Add assertions
            pass
```

Return ONLY the {language} code, no explanations."""

        try:
            self.logger.info(
                "Generating manual tests with optimized prompt",
                requirements_length=len(requirements),
                feature=feature
            )
            
            # Single request for direct code generation
            code = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,  # Use temperature from settings
                max_tokens=max_tokens  # Use max_tokens from settings
            )

            # Clean up code if wrapped in markdown
            if isinstance(code, str):
                # Remove markdown code blocks if present
                if "```python" in code:
                    code = code.split("```python")[1].split("```")[0].strip()
                elif "```" in code:
                    code = code.split("```")[1].split("```")[0].strip()
                
                # Extract test cases info from code for response
                test_cases = self._extract_test_cases_from_code(code)
            else:
                test_cases = []

            generation_time = time.time() - start_time

            self.logger.info(
                "Manual tests generated successfully",
                test_count=len(test_cases),
                generation_time=generation_time
            )

            return {
                "code": code,
                "test_cases": test_cases,
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
        """Validate Python code against testing standards - Fast syntax-only check"""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Quick syntax check using compile
            compile(code, '<string>', 'exec')
            
            # Basic pattern checks
            if '@allure.feature' not in code:
                warnings.append("Missing @allure.feature decorator")
            if '@allure.story' not in code:
                warnings.append("Missing @allure.story decorator")
            if 'def test_' not in code:
                errors.append("No test methods found")
            if 'import allure' not in code:
                errors.append("Missing allure import")
            
            # Check for best practices
            if 'allure.step' not in code:
                suggestions.append("Consider using allure.step for better reporting")
            if '@allure.severity' not in code:
                suggestions.append("Add @allure.severity decorators to tests")
                
            is_valid = len(errors) == 0
            
            return {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }
            
        except SyntaxError as e:
            return {
                "is_valid": False,
                "errors": [f"Syntax error at line {e.lineno}: {e.msg}"],
                "warnings": warnings,
                "suggestions": suggestions
            }
        except Exception as e:
            self.logger.error("Code validation failed", error=str(e))
            return {
                "is_valid": False,
                "errors": [str(e)],
                "warnings": [],
                "suggestions": []
            }

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

    def _extract_test_cases_from_code(self, code: str) -> List[Dict[str, Any]]:
        """Extract test case information from generated Python code"""
        import re
        test_cases = []
        
        # Find all test methods with details
        pattern = r'@allure\.title\("([^"]+)"\)[\s\S]*?@allure\.severity\(Severity\.(\w+)\)[\s\S]*?def (test_\w+)\(self\):\s*"""([^"]*?)"""([\s\S]*?)(?=\n    @allure\.title|class |$)'
        matches = re.finditer(pattern, code)
        
        for match in matches:
            title = match.group(1)
            severity = match.group(2).lower()
            method_name = match.group(3)
            description = match.group(4).strip()
            method_body = match.group(5) if len(match.groups()) > 4 else ""
            
            # Extract steps from allure.step calls
            steps = []
            step_pattern = r'with allure\.step\("([^"]+)"\):'
            step_matches = re.findall(step_pattern, method_body)
            steps = step_matches if step_matches else ["Execute test steps"]
            
            # Find expected result (usually the last step or assertion step)
            expected_result = "Test passes successfully"
            if steps:
                # Look for Assert step
                assert_steps = [s for s in steps if 'assert' in s.lower() or 'проверк' in s.lower()]
                if assert_steps:
                    expected_result = assert_steps[-1]
                else:
                    expected_result = steps[-1]
            
            test_cases.append({
                "title": title,
                "priority": severity,
                "description": description,
                "method_name": method_name,
                "steps": steps,
                "expected_result": expected_result
            })
        
        # Fallback: count def test_ methods if regex didn't work
        if not test_cases:
            test_methods = re.findall(r'def (test_\w+)\(self\):', code)
            for method in test_methods:
                test_cases.append({
                    "title": method.replace('_', ' ').title(),
                    "priority": "normal",
                    "method_name": method,
                    "steps": ["Execute test"],
                    "expected_result": "Test passes"
                })
        
        return test_cases

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
        return re.sub(r'\W+', '_', s2).lower()

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