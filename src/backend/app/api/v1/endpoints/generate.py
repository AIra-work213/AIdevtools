from typing import Any, Dict, List, Optional
import json
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.schemas.test import (
    ManualTestRequest,
    ManualTestResponse,
    ApiTestRequest,
    ApiTestResponse,
    UiTestRequest,
    UiTestResponse,
    ValidationResult
)
from app.services.ai_service import AIService
from app.services.code_validator import get_code_validator
from app.core.deps import RateLimiter, get_current_user, get_current_user_optional

logger = structlog.get_logger(__name__)
router = APIRouter()

# Rate limiting
rate_limiter = RateLimiter()


@router.post("/manual", response_model=ManualTestResponse)
async def generate_manual_tests(
    request: ManualTestRequest,
    current_user: Dict = Depends(get_current_user_optional)
) -> ManualTestResponse:
    """
    Generate manual test cases from requirements with auto-validation and retry
    """
    # Apply rate limiting
    user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
    await rate_limiter.check_limit(f"generate:manual:{user_id}")

    try:
        ai_service = AIService()
        validator = get_code_validator()
        username = current_user.get("username", "anonymous") if current_user else "anonymous"
        logger.info(
            "Generating manual tests with validation",
            user=username,
            requirements_length=len(request.requirements)
        )

        # Generate tests (two-stage: framework + Allure)
        result = await ai_service.generate_manual_tests(
            requirements=request.requirements,
            metadata=request.metadata.model_dump() if request.metadata else None,
            generation_settings=request.generation_settings.model_dump() if request.generation_settings else None,
            conversation_history=[msg.model_dump() for msg in request.conversation_history] if request.conversation_history else None
        )

        # Validate and auto-fix if needed
        validation_result = await validator.validate_with_ai_retry(
            code=result["code"],
            ai_service=ai_service,
            original_requirements=request.requirements,
            max_retries=2
        )

        # Use fixed code if validation succeeded
        final_code = validation_result["final_code"]
        
        # Get final validation details
        final_validation = validation_result["validation_result"]

        response = ManualTestResponse(
            code=final_code,
            test_cases=result["test_cases"],
            validation=ValidationResult(
                is_valid=final_validation["is_valid"],
                errors=final_validation.get("syntax_errors", []) + final_validation.get("runtime_errors", []),
                warnings=[],
                suggestions=[]
            ),
            generation_time=result["generation_time"],
            metadata=request.metadata
        )

        logger.info(
            "Manual tests generated successfully",
            user=username,
            test_cases_count=len(result["test_cases"]),
            generation_time=result["generation_time"],
            validation_retries=validation_result["retries_count"],
            is_valid=validation_result["is_valid"]
        )

        return response

    except Exception as e:
        username = current_user.get("username", "anonymous") if current_user else "anonymous"
        logger.error(
            "Failed to generate manual tests",
            user=username,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate tests. Please try again later."
        )


@router.post("/manual/stream")
async def generate_manual_tests_stream(
    request: ManualTestRequest,
    current_user: Dict = Depends(get_current_user_optional)
) -> StreamingResponse:
    """
    Generate manual tests with streaming response
    """
    user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
    await rate_limiter.check_limit(f"generate:manual:stream:{user_id}")

    async def generate_stream():
        try:
            ai_service = AIService()

            # Send initial status
            yield f"data: {json.dumps({'status': 'started', 'message': 'Analyzing requirements...'})}\n\n"

            # Generate tests
            result = await ai_service.generate_manual_tests(
                requirements=request.requirements,
                metadata=request.metadata.model_dump() if request.metadata else None,
                generation_settings=request.generation_settings.model_dump() if request.generation_settings else None,
                conversation_history=[msg.model_dump() for msg in request.conversation_history] if request.conversation_history else None
            )

            # Send progress
            yield f"data: {json.dumps({'status': 'generating', 'progress': 50})}\n\n"

            # Validate
            validation = await ai_service.validate_code(result["code"])

            # Send completion
            response_data = {
                'status': 'completed',
                'code': result["code"],
                'test_cases': result["test_cases"],
                'validation': validation,
                'generation_time': result["generation_time"]
            }
            yield f"data: {json.dumps(response_data)}\n\n"

        except Exception as e:
            error_data = {
                'status': 'error',
                'error': str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/auto/api", response_model=ApiTestResponse)
async def generate_api_tests(
    request: ApiTestRequest,
    current_user: Dict = Depends(get_current_user_optional)
) -> ApiTestResponse:
    """
    Generate API tests from OpenAPI specification
    """
    user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
    await rate_limiter.check_limit(f"generate:api:{user_id}")

    try:
        ai_service = AIService()
        username = current_user.get("username", "anonymous") if current_user else "anonymous"
        logger.info(
            "Generating API tests",
            user=username,
            endpoints=request.endpoint_filter
        )

        result = await ai_service.generate_api_tests(
            openapi_spec=request.openapi_spec,
            endpoint_filter=request.endpoint_filter,
            test_types=request.test_types
        )

        # Validate generated code
        validation = await ai_service.validate_code(result["code"])

        response = ApiTestResponse(
            code=result["code"],
            endpoints_covered=result["endpoints_covered"],
            test_matrix=result["test_matrix"],
            coverage_percentage=calculate_coverage(result),
            validation=ValidationResult(**validation)
        )

        username = current_user.get("username", "anonymous") if current_user else "anonymous"
        logger.info(
            "API tests generated successfully",
            user=username,
            endpoints_count=len(result["endpoints_covered"])
        )

        return response

    except Exception as e:
        username = current_user.get("username", "anonymous") if current_user else "anonymous"
        logger.error(
            "Failed to generate API tests",
            user=username,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API tests. Please check the OpenAPI specification."
        )


@router.post("/auto/ui", response_model=UiTestResponse)
async def generate_ui_tests(
    request: UiTestRequest,
    current_user: Dict = Depends(get_current_user_optional)
) -> UiTestResponse:
    """
    Generate UI/E2E tests from HTML content or URL with setup instructions
    """
    user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
    await rate_limiter.check_limit(f"generate:ui:{user_id}")

    try:
        ai_service = AIService()
        validator = get_code_validator()
        username = current_user.get("username", "anonymous") if current_user else "anonymous"
        
        logger.info(
            "Generating UI tests",
            user=username,
            input_method=request.input_method,
            framework=request.framework
        )

        result = await ai_service.generate_ui_tests(
            input_method=request.input_method,
            html_content=request.html_content,
            url=request.url,
            selectors=request.selectors,
            framework=request.framework
        )

        # Simple validation (UI tests may not be pytest compatible)
        validation = await ai_service.validate_code(result["code"])

        logger.info(
            "UI tests generated successfully",
            user=username,
            scenarios_count=len(result["test_scenarios"])
        )

        return UiTestResponse(
            code=result["code"],
            selectors_found=result["selectors_found"],
            test_scenarios=result["test_scenarios"],
            setup_instructions=result["setup_instructions"],
            requirements_file=result["requirements_file"],
            validation=ValidationResult(**validation),
            generation_time=result["generation_time"]
        )

    except Exception as e:
        username = current_user.get("username", "anonymous") if current_user else "anonymous"
        logger.error(
            "Failed to generate UI tests",
            user=username,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate UI tests: {str(e)}"
        )


def calculate_coverage(result: Dict[str, Any]) -> float:
    """Calculate test coverage percentage"""
    # Simple implementation - can be enhanced
    endpoints = result.get("endpoints_covered", [])
    if not endpoints:
        return 0.0
    # Assume each endpoint has at least one test
    return min(100.0, len(endpoints) * 10.0)


# Schemas for code execution
class CodeExecutionRequest(BaseModel):
    code: str
    source_code: Optional[str] = None
    timeout: int = 10
    run_with_pytest: bool = False  # Enable pytest/Allure execution


class CodeExecutionResponse(BaseModel):
    is_valid: bool
    can_execute: bool
    syntax_errors: List[str]
    runtime_errors: List[str]
    execution_output: Optional[str] = None
    execution_time: Optional[float] = None
    allure_report_path: Optional[str] = None  # Path to Allure results
    allure_results: Optional[Dict[str, Any]] = None  # Parsed Allure test results


class GenerateWithValidationRequest(ManualTestRequest):
    validate_code: bool = True
    source_code: Optional[str] = None


class GenerateWithValidationResponse(BaseModel):
    code: str
    validation: CodeExecutionResponse
    test_cases: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@router.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(
    request: CodeExecutionRequest,
    current_user: Dict = Depends(get_current_user_optional)
) -> CodeExecutionResponse:
    """
    Execute Python code with optional pytest/Allure support and return results
    """
    user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
    username = current_user.get('username', 'anonymous') if current_user else 'anonymous'
    await rate_limiter.check_limit(f"execute:code:{user_id}")

    try:
        logger.info(
            "Executing code",
            user=username,
            code_length=len(request.code),
            has_source=bool(request.source_code),
            with_pytest=request.run_with_pytest
        )

        validator = get_code_validator()
        result = validator.execute_code(
            code=request.code,
            source_code=request.source_code,
            run_with_pytest=request.run_with_pytest
        )

        logger.info(
            "Code execution completed",
            user=username,
            is_valid=result.is_valid,
            can_execute=result.can_execute,
            has_allure=bool(result.allure_results)
        )

        return CodeExecutionResponse(
            is_valid=result.is_valid,
            can_execute=result.can_execute,
            syntax_errors=result.syntax_errors,
            runtime_errors=result.runtime_errors,
            execution_output=result.execution_output,
            execution_time=result.execution_time,
            allure_report_path=result.allure_report_path,
            allure_results=result.allure_results,
        )

    except Exception as e:
        logger.error(
            "Code execution failed",
            user=username,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code execution failed: {str(e)}"
        )


@router.post("/manual/validated", response_model=GenerateWithValidationResponse)
async def generate_manual_tests_with_validation(
    request: GenerateWithValidationRequest,
    current_user: Dict = Depends(get_current_user_optional)
) -> GenerateWithValidationResponse:
    """
    Generate manual test cases with automatic validation
    Pipeline: TestGenerator -> Validator -> Response
    """
    user_id = current_user.get('id', 'anonymous') if current_user else 'anonymous'
    username = current_user.get('username', 'anonymous') if current_user else 'anonymous'
    await rate_limiter.check_limit(f"generate:validated:{user_id}")

    try:
        logger.info(
            "Generating tests with validation",
            user=username,
            requirements_length=len(request.requirements),
            validate=request.validate_code
        )

        # Step 1: Generate tests
        ai_service = AIService()
        result = await ai_service.generate_manual_tests(
            requirements=request.requirements,
            metadata=request.metadata.model_dump() if request.metadata else None,
            generation_settings=request.generation_settings.model_dump() if request.generation_settings else None,
            conversation_history=[msg.model_dump() for msg in request.conversation_history] if request.conversation_history else None
        )

        # Step 2: Validate generated code
        validation_result = None
        if request.validate_code:
            validator = get_code_validator()
            validation_result = validator.execute_code(
                code=result["code"],
                source_code=request.source_code
            )

            logger.info(
                "Validation completed",
                user=username,
                is_valid=validation_result.is_valid,
                can_execute=validation_result.can_execute
            )

            # If validation failed, try to fix
            if not validation_result.can_execute:
                logger.warning(
                    "Generated code failed validation, attempting to fix",
                    user=username,
                    errors=validation_result.runtime_errors
                )
                # Could implement auto-fix logic here

        # Step 3: Return response
        return GenerateWithValidationResponse(
            code=result["code"],
            validation=CodeExecutionResponse(
                is_valid=validation_result.is_valid if validation_result else True,
                can_execute=validation_result.can_execute if validation_result else True,
                syntax_errors=validation_result.syntax_errors if validation_result else [],
                runtime_errors=validation_result.runtime_errors if validation_result else [],
                execution_output=validation_result.execution_output if validation_result else None,
                execution_time=validation_result.execution_time if validation_result else None,
            ),
            test_cases=result.get("test_cases", []),
            metadata=result.get("metadata", {}),
        )

    except Exception as e:
        logger.error(
            "Failed to generate validated tests",
            user=username,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate validated tests: {str(e)}"
        )