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

    async def generate_code(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate code using LLM chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated code as string
        """
        try:
            code = await self.llm_client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Clean up code if wrapped in markdown
            if isinstance(code, str):
                code = code.strip()
                # Remove markdown code blocks if present
                if "```python" in code:
                    code = code.split("```python")[1].split("```")[0].strip()
                elif "```" in code:
                    code = code.split("```")[1].split("```")[0].strip()
            
            return code
            
        except Exception as e:
            self.logger.error("Failed to generate code", error=str(e))
            raise

    async def generate_manual_tests(
        self,
        requirements: str,
        metadata: Optional[Dict[str, Any]] = None,
        generation_settings: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate manual tests from requirements - TWO-STAGE GENERATION
        Stage 1: Generate tests using framework from settings
        Stage 2: Wrap tests with Allure decorators
        """
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

        # Extract metadata
        feature = metadata.get("feature", "User Generated") if metadata else "User Generated"
        owner = metadata.get("owner", "QA Engineer") if metadata else "QA Engineer"

        # Build context from conversation history
        context = ""
        if conversation_history and len(conversation_history) > 0:
            context = "\n\nPrevious conversation context:\n"
            for msg in conversation_history[-5:]:  # Use last 5 messages for context
                context += f"{msg['type'].upper()}: {msg['content']}\n"
            context += "\n"

        try:
            # ============ STAGE 1: Generate base tests with framework ============
            self.logger.info(
                "STAGE 1: Generating base tests with framework",
                framework=framework,
                requirements_length=len(requirements)
            )

            stage1_system = f"""You are an expert QA engineer specializing in {framework} test automation.
Generate clean, functional tests using {framework} framework WITHOUT Allure decorators.
Focus on test logic, assertions, and {framework} best practices."""

            # Build detailed instructions
            instructions = []
            if detail_level == "minimal":
                instructions.append("Generate minimal tests with only essential test cases")
            elif detail_level == "detailed":
                instructions.append("Generate comprehensive tests with many edge cases")
            else:
                instructions.append("Generate standard tests covering main scenarios")

            if use_aaa:
                instructions.append("Use Arrange-Act-Assert pattern")
            if include_negative:
                instructions.append("Include negative test scenarios")

            stage1_user = f"""Generate {framework} test code for these requirements:

{context}
Current requirements:
{requirements}

Instructions:
{chr(10).join(f"- {inst}" for inst in instructions)}

Generate a complete test class with:
1. Import {framework} (NO Allure imports yet)
2. Test class
3. Multiple test methods (def test_*) covering:
   - Happy path scenarios
   - Edge cases
   {"   - Error conditions" if include_negative else ""}
4. Each test should have:
   - Clear descriptive name
   - Docstring explaining the test
   {"   - AAA pattern (Arrange, Act, Assert)" if use_aaa else ""}
   - Proper assertions

Return ONLY {language} code, no markdown, no explanations."""

            base_code = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": stage1_system},
                    {"role": "user", "content": stage1_user}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Clean code from markdown
            if isinstance(base_code, str):
                if "```python" in base_code:
                    base_code = base_code.split("```python")[1].split("```")[0].strip()
                elif "```" in base_code:
                    base_code = base_code.split("```")[1].split("```")[0].strip()
            
            self.logger.info("STAGE 1 completed", code_length=len(base_code))

            # ============ STAGE 2: Wrap with Allure decorators ============
            self.logger.info("STAGE 2: Wrapping tests with Allure decorators")

            stage2_system = """You are an expert in Allure test reporting framework.
Your task is to add Allure decorators to existing tests WITHOUT changing test logic."""

            stage2_user = f"""Add Allure decorators to this test code:

```python
{base_code}
```

Requirements:
1. Add imports: allure, allure_commons.types.Severity
2. Add class decorators:
   - @allure.feature("{feature}")
   - @allure.story("Test Scenarios")
   - @allure.label("owner", "{owner}")
   - @allure.tag("generated_by_ai")
3. For EACH test method add:
   - @allure.title("Clear test description")
   - @allure.severity(Severity.NORMAL or HIGH or CRITICAL based on importance)
   - @allure.manual
4. Wrap test steps with allure.step():
   - with allure.step("Arrange: Setup"): ...
   - with allure.step("Act: Perform action"): ...
   - with allure.step("Assert: Verify result"): ...

IMPORTANT:
- Keep ALL original test logic unchanged
- Keep ALL assertions unchanged
- Only ADD Allure decorators and step wrappers
- Return complete working code

Return ONLY Python code, no markdown, no explanations."""

            final_code = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": stage2_system},
                    {"role": "user", "content": stage2_user}
                ],
                temperature=0.2,  # Lower temperature for more precise wrapping
                max_tokens=max_tokens
            )

            # Clean final code
            if isinstance(final_code, str):
                if "```python" in final_code:
                    final_code = final_code.split("```python")[1].split("```")[0].strip()
                elif "```" in final_code:
                    final_code = final_code.split("```")[1].split("```")[0].strip()

            self.logger.info("STAGE 2 completed", final_code_length=len(final_code))

            # Extract test cases from final code
            test_cases = self._extract_test_cases_from_code(final_code)
            generation_time = time.time() - start_time

            self.logger.info(
                "Two-stage generation completed successfully",
                test_count=len(test_cases),
                generation_time=generation_time
            )

            return {
                "code": final_code,
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
        """Generate API tests from OpenAPI specification - TWO-STAGE GENERATION
        Stage 1: Generate base API tests with pytest/requests
        Stage 2: Wrap with Allure decorators
        """
        start_time = time.time()

        try:
            # Parse OpenAPI first for context
            parsed_spec = await self._parse_openapi_spec(openapi_spec)

            # ============ STAGE 1: Generate base API tests ============
            self.logger.info("STAGE 1: Generating base API tests")

            stage1_system = """You are an expert API testing engineer specializing in pytest and requests library.
Generate clean, functional API tests WITHOUT Allure decorators.
Focus on HTTP requests, response validation, and pytest assertions."""

            stage1_user = f"""Generate pytest API tests for this OpenAPI specification:

```yaml
{openapi_spec}
```

{f'Focus on endpoints: {endpoint_filter}' if endpoint_filter else ''}
{f'Test types: {test_types}' if test_types else 'Include: positive, negative, edge cases'}

Requirements:
1. Import pytest, requests (NO Allure yet)
2. Create test class
3. For each endpoint generate tests for:
   - Happy path (valid requests, 200/201 responses)
   - Validation (invalid data, 400/422 responses)
   - Authorization (401/403 if auth required)
   - Edge cases (boundary values)
4. Use pytest fixtures for setup
5. Clear assertions on status codes and response schemas

Return ONLY Python code, no markdown, no explanations."""

            base_code = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": stage1_system},
                    {"role": "user", "content": stage1_user}
                ],
                temperature=0.3,
                max_tokens=8000
            )

            # Clean code
            if isinstance(base_code, str):
                if "```python" in base_code:
                    base_code = base_code.split("```python")[1].split("```")[0].strip()
                elif "```" in base_code:
                    base_code = base_code.split("```")[1].split("```")[0].strip()

            self.logger.info("STAGE 1 completed", code_length=len(base_code))

            # ============ STAGE 2: Wrap with Allure decorators ============
            self.logger.info("STAGE 2: Wrapping with Allure decorators")

            stage2_system = """You are an expert in Allure test reporting.
Add Allure decorators to existing API tests WITHOUT changing test logic."""

            stage2_user = f"""Add Allure decorators to this API test code:

```python
{base_code}
```

Requirements:
1. Add imports: allure, allure_commons.types.Severity
2. Add class decorators:
   - @allure.feature("API Testing")
   - @allure.story("REST API Endpoints")
   - @allure.tag("api", "generated_by_ai")
3. For EACH test method add:
   - @allure.title("Endpoint: {{method}} {{path}} - {{scenario}}")
   - @allure.severity(Severity.CRITICAL for auth/happy path, HIGH for validation, NORMAL for edge cases)
4. Wrap key steps:
   - with allure.step("Send {{method}} request to {{endpoint}}"): ...
   - with allure.step("Validate status code"): ...
   - with allure.step("Validate response schema"): ...

Keep ALL test logic unchanged. Return ONLY Python code."""

            final_code = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": stage2_system},
                    {"role": "user", "content": stage2_user}
                ],
                temperature=0.2,
                max_tokens=8000
            )

            # Clean final code
            if isinstance(final_code, str):
                if "```python" in final_code:
                    final_code = final_code.split("```python")[1].split("```")[0].strip()
                elif "```" in final_code:
                    final_code = final_code.split("```")[1].split("```")[0].strip()

            self.logger.info("STAGE 2 completed", final_code_length=len(final_code))

            # Extract endpoints covered
            endpoints_covered = self._extract_endpoints_from_code(final_code)
            generation_time = time.time() - start_time

            return {
                "code": final_code,
                "endpoints_covered": endpoints_covered,
                "test_matrix": self._build_api_test_matrix(final_code),
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

    async def _parse_openapi_spec(self, spec: str) -> Dict[str, Any]:
        """Parse OpenAPI specification (JSON or YAML)"""
        import json
        try:
            return json.loads(spec)
        except json.JSONDecodeError:
            # Try YAML parsing
            try:
                import yaml
                return yaml.safe_load(spec)
            except Exception:
                raise ValueError("Invalid OpenAPI specification format")

    async def _generate_api_code_from_structure(
        self,
        structure: Dict[str, Any],
        parsed_spec: Dict[str, Any]
    ) -> str:
        """Generate Python API test code from structured data"""
        endpoints = structure.get("endpoints", [])
        
        code_lines = [
            "import pytest",
            "import requests",
            "from typing import Dict, Any",
            "",
            "",
            "BASE_URL = 'http://localhost:8000'  # Change to your API URL",
            "",
            ""
        ]
        
        for endpoint in endpoints:
            path = endpoint.get("path", "/")
            method = endpoint.get("method", "GET").upper()
            test_name = f"test_{method.lower()}_{path.replace('/', '_').strip('_')}"
            
            code_lines.append(f"def {test_name}():")
            code_lines.append(f'    """Test {method} {path}"""')
            code_lines.append(f"    url = BASE_URL + '{path}'")
            code_lines.append("")
            
            if method == "GET":
                code_lines.append("    response = requests.get(url)")
            elif method == "POST":
                code_lines.append("    data = {}")
                code_lines.append("    response = requests.post(url, json=data)")
            elif method == "PUT":
                code_lines.append("    data = {}")
                code_lines.append("    response = requests.put(url, json=data)")
            elif method == "DELETE":
                code_lines.append("    response = requests.delete(url)")
            
            code_lines.append("")
            code_lines.append("    assert response.status_code in [200, 201, 204]")
            code_lines.append("")
            code_lines.append("")
        
        return "\n".join(code_lines)

    async def _generate_api_code_directly(self, spec: str) -> str:
        """Generate API test code directly using AI"""
        prompt = f"""
Generate Python pytest code for API testing based on this OpenAPI specification:

{spec}

Use requests library. Include:
1. BASE_URL configuration
2. Test functions for each endpoint
3. Proper assertions for status codes
4. JSON payload examples
"""
        
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are an expert API testing engineer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Clean markdown
        code = response.get("content", "")
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        return code.strip()

    async def generate_ui_tests(
        self,
        input_method: str,
        html_content: Optional[str] = None,
        url: Optional[str] = None,
        selectors: Optional[Dict[str, str]] = None,
        framework: str = "playwright"
    ) -> Dict[str, Any]:
        """Generate UI/E2E tests - TWO-STAGE + ADAPTIVE GENERATION
        Stage 0 (if URL): Analyze website to discover pages/links
        Stage 1: Generate base UI tests
        Stage 2: Wrap with Allure decorators (Python only)
        """
        start_time = time.time()
        
        # Language mapping
        language_map = {
            "playwright": "python",
            "selenium": "python",
            "cypress": "javascript"
        }
        language = language_map.get(framework, "python")
        
        # ============ STAGE 0: ADAPTIVE URL ANALYSIS (if URL provided) ============
        discovered_urls = []
        site_structure = {}
        
        if input_method == "url" and url:
            self.logger.info("STAGE 0: Analyzing website structure", url=url)
            try:
                site_analysis = await self._analyze_website_structure(url)
                discovered_urls = site_analysis.get("discovered_urls", [])
                site_structure = site_analysis.get("structure", {})
                self.logger.info(
                    "Website analysis completed",
                    pages_found=len(discovered_urls),
                    structure_depth=len(site_structure)
                )
            except Exception as e:
                self.logger.warning("Website analysis failed, continuing with single URL", error=str(e))
                discovered_urls = [url]
        
        # ============ STAGE 1: Generate base UI tests ============
        self.logger.info("STAGE 1: Generating base UI tests", framework=framework)
        
        stage1_system = f"""You are an expert in UI/E2E testing with {framework}.
Generate clean, functional UI tests WITHOUT Allure decorators (for Python) or reporting tools.
Focus on test logic, element interactions, and {framework} best practices."""
        
        # Build adaptive prompt based on discovered URLs
        adaptive_context = ""
        if discovered_urls and len(discovered_urls) > 1:
            adaptive_context = f"""

WEBSITE STRUCTURE DISCOVERED:
The target website has {len(discovered_urls)} pages:
{chr(10).join(f"- {u}" for u in discovered_urls[:10])}

Generate SEPARATE test scenarios for DIFFERENT pages:
- Create specific tests for each unique page URL
- Test page-specific functionality (forms, buttons, navigation on that page)
- Verify page-specific content and elements
- Include inter-page navigation tests
"""
        
        if input_method == "html":
            stage1_user = f"""Generate {framework} tests in {language} for this HTML:

```html
{html_content}
```

{f'Focus on these selectors: {selectors}' if selectors else ''}

Include:
- Complete test file with imports ({framework}, pytest for Python)
- Setup and teardown fixtures
- Multiple test scenarios
- Proper assertions
- NO Allure decorators yet

Return ONLY code, no markdown, no explanations."""
        else:
            # Special headless configuration for Selenium
            headless_config = ""
            if framework == "selenium":
                headless_config = """

CRITICAL: Configure Selenium for HEADLESS mode (Docker/CI compatible):
```python
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')

driver = webdriver.Chrome(options=options)
```
Use this configuration in ALL test fixtures!"""

            stage1_user = f"""Generate {framework} tests in {language} for the website.

BASE URL: {url}
{adaptive_context}
{headless_config}

{f'Focus on these selectors: {selectors}' if selectors else ''}

Include:
- Complete test file with imports ({framework}, pytest for Python)
- Setup and teardown fixtures with HEADLESS browser configuration
- Multiple test scenarios covering DIFFERENT pages from the site
- Each test should target a SPECIFIC URL from the discovered pages
- Proper assertions
- NO Allure decorators yet

Return ONLY code, no markdown, no explanations."""
        
        try:
            base_code = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": stage1_system},
                    {"role": "user", "content": stage1_user}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # Clean code
            if isinstance(base_code, str):
                if "```" in base_code:
                    parts = base_code.split("```")
                    for i, part in enumerate(parts):
                        if i % 2 == 1:  # Code block
                            lines = part.split("\n")
                            if lines[0].strip() in ["python", "typescript", "javascript", framework, language]:
                                base_code = "\n".join(lines[1:])
                            else:
                                base_code = part
                            break
            
            self.logger.info("STAGE 1 completed", code_length=len(base_code))
            
            # ============ STAGE 2: Wrap with Allure (Python only) ============
            final_code = base_code
            
            if framework in ["playwright", "selenium"]:  # Python frameworks
                self.logger.info("STAGE 2: Wrapping with Allure decorators")
                
                stage2_system = """You are an expert in Allure test reporting.
Add Allure decorators to existing UI tests WITHOUT changing test logic."""
                
                stage2_user = f"""Add Allure decorators to this {framework} test code:

```python
{base_code}
```

Requirements:
1. Add imports: allure, allure_commons.types.Severity
2. Add class decorators:
   - @allure.feature("UI Testing")
   - @allure.story("User Workflows")
   - @allure.tag("ui", "e2e", "generated_by_ai")
3. For EACH test method add:
   - @allure.title("Test {{page/functionality}}")
   - @allure.severity(Severity.CRITICAL for login/main flows, HIGH for forms, NORMAL for navigation)
4. Wrap test steps:
   - with allure.step("Navigate to {{url}}"): ...
   - with allure.step("Interact with {{element}}"): ...
   - with allure.step("Verify {{condition}}"): ...

Keep ALL test logic unchanged. Return ONLY Python code, no markdown."""
                
                final_code = await self.llm_client.chat_completion(
                    messages=[
                        {"role": "system", "content": stage2_system},
                        {"role": "user", "content": stage2_user}
                    ],
                    temperature=0.2,
                    max_tokens=4000
                )
                
                # Clean final code
                if isinstance(final_code, str):
                    if "```python" in final_code:
                        final_code = final_code.split("```python")[1].split("```")[0].strip()
                    elif "```" in final_code:
                        final_code = final_code.split("```")[1].split("```")[0].strip()
                
                self.logger.info("STAGE 2 completed", final_code_length=len(final_code))
            
            # Extract selectors and scenarios
            selectors_found = self._extract_selectors_from_code(final_code, framework)
            test_scenarios = self._extract_test_scenarios(final_code)
            
            # Generate setup instructions and requirements
            setup_instructions = self._generate_setup_instructions(framework, language)
            requirements_file = self._generate_requirements(framework, language)
            
            generation_time = time.time() - start_time
            
            result = {
                "code": final_code.strip(),
                "selectors_found": selectors_found,
                "test_scenarios": test_scenarios,
                "setup_instructions": setup_instructions,
                "requirements_file": requirements_file,
                "generation_time": generation_time
            }
            
            # Add discovered URLs if adaptive analysis was performed
            if discovered_urls:
                result["discovered_urls"] = discovered_urls
                result["pages_tested"] = len(discovered_urls)
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to generate UI tests", error=str(e))
            raise

    async def _analyze_website_structure(self, url: str) -> Dict[str, Any]:
        """Analyze website structure to discover pages and links (adaptive generation)"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin, urlparse
            
            discovered_urls = set()
            base_domain = urlparse(url).netloc
            
            async with aiohttp.ClientSession() as session:
                # Fetch main page
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find all links
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            full_url = urljoin(url, href)
                            parsed = urlparse(full_url)
                            
                            # Only include same-domain links
                            if parsed.netloc == base_domain:
                                # Clean URL (remove fragments, query params for cleaner list)
                                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                                if clean_url.endswith('/'):
                                    clean_url = clean_url[:-1]
                                discovered_urls.add(clean_url)
                        
                        # Limit to reasonable number
                        discovered_urls = list(discovered_urls)[:15]
                        
                        # Categorize pages
                        structure = {
                            "total_links": len(discovered_urls),
                            "main_page": url,
                            "subpages": [u for u in discovered_urls if u != url]
                        }
                        
                        return {
                            "discovered_urls": [url] + structure["subpages"],
                            "structure": structure
                        }
            
            # Fallback if analysis fails
            return {
                "discovered_urls": [url],
                "structure": {"total_links": 1, "main_page": url, "subpages": []}
            }
            
        except Exception as e:
            self.logger.warning("Website structure analysis failed", error=str(e))
            return {
                "discovered_urls": [url],
                "structure": {"total_links": 1, "main_page": url, "subpages": []}
            }

    def _extract_selectors_from_code(self, code: str, framework: str) -> List[str]:
        """Extract selectors from generated code"""
        import re
        selectors = []
        
        if framework == "playwright":
            # Extract playwright selectors
            patterns = [
                r'page\.locator\(["\']([^"\']+)["\']\)',
                r'page\.get_by_[a-z]+\(["\']([^"\']+)["\']\)',
            ]
        elif framework == "selenium":
            patterns = [
                r'find_element\(By\.[A-Z_]+,\s*["\']([^"\']+)["\']\)',
            ]
        else:  # cypress
            patterns = [
                r'cy\.get\(["\']([^"\']+)["\']\)',
            ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code)
            selectors.extend(matches)
        
        return list(set(selectors))[:10]  # Return up to 10 unique selectors

    def _extract_test_scenarios(self, code: str) -> List[str]:
        """Extract test scenario descriptions from code"""
        import re
        scenarios = []
        
        # Extract test function names and docstrings
        test_pattern = r'(?:test|it)\(["\']([^"\']+)["\']\)|(?:def|async def)\s+(test_\w+)|"""([^"]+)"""'
        matches = re.findall(test_pattern, code)
        
        for match in matches:
            scenario = next((m for m in match if m), None)
            if scenario and scenario.strip():
                # Clean up scenario name
                scenario = scenario.replace('test_', '').replace('_', ' ').title()
                if len(scenario) > 5:  # Skip very short matches
                    scenarios.append(scenario)
        
        return list(set(scenarios))[:10]  # Return up to 10 unique scenarios

    def _generate_requirements(self, framework: str, language: str) -> str:
        """Generate requirements.txt content for UI tests"""
        
        requirements = {
            "playwright": """# UI Testing with Playwright
pytest==7.4.3
pytest-playwright==0.4.3
playwright==1.40.0
pytest-asyncio==0.21.1
pytest-xdist==3.5.0
allure-pytest==2.15.2

# Additional utilities
python-dotenv==1.0.0
Pillow==10.1.0""",
            "selenium": """# UI Testing with Selenium
pytest==7.4.3
selenium==4.15.2
webdriver-manager==4.0.1
pytest-asyncio==0.21.1
pytest-xdist==3.5.0
allure-pytest==2.15.2

# Additional utilities
python-dotenv==1.0.0
Pillow==10.1.0""",
            "cypress": """# UI Testing with Cypress (Node.js)
# Note: Cypress requires Node.js and npm
# Install via: npm install --save-dev cypress@13.6.0
# These Python packages are for pytest integration if needed:
pytest==7.4.3
pytest-asyncio==0.21.1"""
        }
        
        return requirements.get(framework, "# No requirements specified")

    def _generate_setup_instructions(self, framework: str, language: str) -> str:
        """Generate setup instructions for UI test execution"""
        
        instructions = {
            "playwright": f"""# Инструкция по запуску UI тестов (Playwright)

## 1. Установка зависимостей

### Вариант А: Использование глобальной среды (рекомендуется)
```bash
# Активируйте глобальную UI-testing среду
source ~/ui-testing-env/bin/activate  # Linux/Mac
# или
~/ui-testing-env/Scripts/activate  # Windows

# Браузеры уже установлены в глобальной среде!
```

### Вариант Б: Локальная установка
```bash
# Установите из сгенерированного requirements.txt
pip install -r requirements.txt

# Установите браузеры
playwright install
```

## 2. Запуск тестов

```bash
# Запустить все тесты
pytest test_ui.py -v

# Запустить с видимым браузером (headed mode)
pytest test_ui.py --headed

# Запустить в определенном браузере
pytest test_ui.py --browser chromium
pytest test_ui.py --browser firefox
pytest test_ui.py --browser webkit

# Запустить с замедлением (для отладки)
pytest test_ui.py --slowmo 1000
```

## 3. Дополнительные опции

```bash
# Сделать скриншоты при падении
pytest test_ui.py --screenshot on

# Записать видео
pytest test_ui.py --video on

# Запустить в debug режиме
PWDEBUG=1 pytest test_ui.py
```
""",
            "selenium": f"""# Инструкция по запуску UI тестов (Selenium)

## 1. Установка зависимостей

### Вариант А: Использование глобальной среды (рекомендуется)
```bash
# Активируйте глобальную UI-testing среду
source ~/ui-testing-env/bin/activate  # Linux/Mac
# или
~/ui-testing-env/Scripts/activate  # Windows

# Все драйвера установятся автоматически при первом запуске!
```

### Вариант Б: Локальная установка
```bash
# Установите из сгенерированного requirements.txt
pip install -r requirements.txt
```

## 2. Запуск тестов

```bash
# Запустить все тесты
pytest test_ui.py -v

# Запустить с конкретным браузером (настройте в conftest.py)
pytest test_ui.py --browser chrome
pytest test_ui.py --browser firefox

# Запустить headless
pytest test_ui.py --headless
```

## 3. Структура conftest.py

Создайте файл `conftest.py` рядом с тестами:

```python
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

@pytest.fixture
def browser():
    options = Options()
    options.add_argument('--headless')  # Headless режим
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()
```

**Для Docker/CI:**
```python
@pytest.fixture
def browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = '/usr/bin/google-chrome'  # Chrome в Docker
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()
```
""",
            "cypress": f"""# Инструкция по запуску UI тестов (Cypress)

## 1. Установка зависимостей

### Вариант А: Глобальная установка (рекомендуется)
```bash
# Установите Cypress глобально (один раз)
npm install -g cypress@13.6.0

# Cypress уже готов к использованию!
```

### Вариант Б: Локальная установка
```bash
# Установите в проект
npm install --save-dev cypress
# или
yarn add --dev cypress
```

## 2. Запуск тестов

```bash
# Открыть Cypress UI
npx cypress open

# Запустить headless
npx cypress run

# Запустить конкретный файл
npx cypress run --spec "cypress/e2e/test_ui.cy.js"

# Запустить в определенном браузере
npx cypress run --browser chrome
npx cypress run --browser firefox
```

## 3. Структура проекта

```
cypress/
  ├── e2e/
  │   └── test_ui.cy.js
  ├── fixtures/
  └── support/
      ├── commands.js
      └── e2e.js
```

## 4. Дополнительные опции

```bash
# Запустить с видео
npx cypress run --video

# Запустить с конфигурацией
npx cypress run --config viewportWidth=1920,viewportHeight=1080
```
"""
        }
        
        return instructions.get(framework, "No setup instructions available for this framework.")

    def _extract_endpoints_from_code(self, code: str) -> List[str]:
        """Extract API endpoints from generated test code"""
        import re
        endpoints = []
        
        # Find URL patterns in requests calls
        patterns = [
            r'requests\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'url\s*=\s*["\']([^"\']+)["\']',
            r'BASE_URL\s*\+\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                endpoint = match if isinstance(match, str) else match[-1]
                if endpoint and endpoint.startswith('/'):
                    endpoints.append(endpoint)
        
        return list(set(endpoints))[:20]  # Return up to 20 unique endpoints

    def _build_api_test_matrix(self, code: str) -> Dict[str, List[str]]:
        """Build test matrix from generated API test code"""
        import re
        matrix = {}
        
        # Find test functions with their endpoints
        test_pattern = r'def (test_\w+)\([^)]*\):[\s\S]*?url.*?["\']([^"\']+)["\']'
        matches = re.findall(test_pattern, code)
        
        for test_name, endpoint in matches:
            if endpoint not in matrix:
                matrix[endpoint] = []
            # Clean test name
            scenario = test_name.replace('test_', '').replace('_', ' ').title()
            matrix[endpoint].append(scenario)
        
        return matrix


# Create singleton instance
ai_service = AIService()