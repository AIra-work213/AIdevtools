from typing import Any, Dict, List
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas.test import (
    ManualTestRequest,
    ManualTestResponse,
    ApiTestRequest,
    ApiTestResponse,
    ValidationResult
)
from app.services.ai_service import AIService
from app.core.deps import RateLimiter, get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()

# Rate limiting
rate_limiter = RateLimiter()


@router.post("/manual", response_model=ManualTestResponse)
async def generate_manual_tests(
    request: ManualTestRequest,
    current_user: Dict = Depends(get_current_user)
) -> ManualTestResponse:
    """
    Generate manual test cases from requirements
    """
    # Apply rate limiting
    await rate_limiter.check_limit(f"generate:manual:{current_user['id']}")

    try:
        ai_service = AIService()
        logger.info(
            "Generating manual tests",
            user=current_user["username"],
            requirements_length=len(request.requirements)
        )

        result = await ai_service.generate_manual_tests(
            requirements=request.requirements,
            metadata=request.metadata.dict() if request.metadata else None
        )

        # Validate generated code
        validation = await ai_service.validate_code(result["code"])

        response = ManualTestResponse(
            code=result["code"],
            test_cases=result["test_cases"],
            validation=ValidationResult(**validation),
            generation_time=result["generation_time"],
            metadata=request.metadata
        )

        logger.info(
            "Manual tests generated successfully",
            user=current_user["username"],
            test_cases_count=len(result["test_cases"]),
            generation_time=result["generation_time"]
        )

        return response

    except Exception as e:
        logger.error(
            "Failed to generate manual tests",
            user=current_user["username"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate tests. Please try again later."
        )


@router.post("/manual/stream")
async def generate_manual_tests_stream(
    request: ManualTestRequest,
    current_user: Dict = Depends(get_current_user)
) -> StreamingResponse:
    """
    Generate manual tests with streaming response
    """
    await rate_limiter.check_limit(f"generate:manual:stream:{current_user['id']}")

    async def generate_stream():
        try:
            ai_service = AIService()

            # Send initial status
            yield f"data: {json.dumps({'status': 'started', 'message': 'Analyzing requirements...'})}\n\n"

            # Generate tests
            result = await ai_service.generate_manual_tests(
                requirements=request.requirements,
                metadata=request.metadata.dict() if request.metadata else None
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
    current_user: Dict = Depends(get_current_user)
) -> ApiTestResponse:
    """
    Generate API tests from OpenAPI specification
    """
    await rate_limiter.check_limit(f"generate:api:{current_user['id']}")

    try:
        ai_service = AIService()
        logger.info(
            "Generating API tests",
            user=current_user["username"],
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

        logger.info(
            "API tests generated successfully",
            user=current_user["username"],
            endpoints_count=len(result["endpoints_covered"])
        )

        return response

    except Exception as e:
        logger.error(
            "Failed to generate API tests",
            user=current_user["username"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API tests. Please check the OpenAPI specification."
        )


@router.post("/auto/ui")
async def generate_ui_tests(
    html_content: str,
    selectors: Dict[str, str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate UI/E2E tests from HTML content or selectors
    """
    await rate_limiter.check_limit(f"generate:ui:{current_user['id']}")

    # TODO: Implement UI test generation
    return {"status": "not_implemented"}


def calculate_coverage(result: Dict[str, Any]) -> float:
    """Calculate test coverage percentage"""
    # Simple implementation - can be enhanced
    endpoints = result.get("endpoints_covered", [])
    if not endpoints:
        return 0.0
    # Assume each endpoint has at least one test
    return min(100.0, len(endpoints) * 10.0)