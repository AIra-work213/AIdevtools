from typing import Any, Dict, List
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
import ast

from app.schemas.test import (
    ValidationRequest,
    ValidationResponse,
    DuplicateSearchRequest,
    DuplicateSearchResponse,
    TestCase,
    DuplicateGroup,
    SimilarTestCase
)
from app.services.ai_service import AIService
from app.services.validation_service import ValidationService
from app.services.duplicate_service import DuplicateService
from app.core.deps import get_current_user, RateLimiter

logger = structlog.get_logger(__name__)
router = APIRouter()
rate_limiter = RateLimiter()


@router.post("/validate", response_model=ValidationResponse)
async def validate_code(
    request: ValidationRequest,
    current_user: Dict = Depends(get_current_user)
) -> ValidationResponse:
    """
    Validate Python test code against standards
    """
    await rate_limiter.check_limit(f"validate:code:{current_user['id']}")

    try:
        # First, check syntax
        syntax_valid = True
        syntax_errors = []
        try:
            ast.parse(request.code)
        except SyntaxError as e:
            syntax_valid = False
            syntax_errors.append({
                "type": "SyntaxError",
                "message": str(e),
                "line": e.lineno,
                "column": e.offset
            })

        if not syntax_valid:
            return ValidationResponse(
                is_valid=False,
                errors=[{
                    "type": "syntax",
                    "message": f"Syntax error: {e.msg}",
                    "line": e.lineno,
                    "column": e.offset
                } for e in syntax_errors],
                warnings=[],
                suggestions=["Fix syntax errors before validation"],
                metrics={}
            )

        # Use AI service for deeper validation
        ai_service = AIService()
        validation_result = await ai_service.validate_code(
            code=request.code,
            standards=request.standards
        )

        # Use validation service for structural checks
        val_service = ValidationService()
        structural_result = await val_service.validate_structure(
            code=request.code,
            standards=request.standards,
            strict_mode=request.strict_mode
        )

        # Merge results
        all_errors = validation_result.get("errors", []) + structural_result.get("errors", [])
        all_warnings = validation_result.get("warnings", []) + structural_result.get("warnings", [])
        all_suggestions = validation_result.get("suggestions", []) + structural_result.get("suggestions", [])

        # Calculate metrics
        metrics = val_service.calculate_metrics(request.code)

        response = ValidationResponse(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            metrics=metrics
        )

        logger.info(
            "Code validation completed",
            user=current_user["username"],
            is_valid=response.is_valid,
            errors_count=len(all_errors),
            warnings_count=len(all_warnings)
        )

        return response

    except Exception as e:
        logger.error(
            "Code validation failed",
            user=current_user["username"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate code"
        )


@router.post("/duplicates", response_model=DuplicateSearchResponse)
async def find_duplicates(
    request: DuplicateSearchRequest,
    current_user: Dict = Depends(get_current_user)
) -> DuplicateSearchResponse:
    """
    Find duplicate or similar test cases
    """
    await rate_limiter.check_limit(f"duplicates:search:{current_user['id']}")

    try:
        duplicate_service = DuplicateService()
        logger.info(
            "Searching for duplicate tests",
            user=current_user["username"],
            test_cases_count=len(request.test_cases),
            threshold=request.similarity_threshold
        )

        duplicates = await duplicate_service.find_duplicates(
            test_cases=request.test_cases,
            threshold=request.similarity_threshold
        )

        # Build similarity matrix for detailed analysis
        similarity_matrix = duplicate_service.build_similarity_matrix(
            request.test_cases
        )

        response = DuplicateSearchResponse(
            duplicates=duplicates,
            total_tests=len(request.test_cases),
            duplicates_found=len(duplicates),
            similarity_matrix=similarity_matrix if len(request.test_cases) <= 50 else None
        )

        logger.info(
            "Duplicate search completed",
            user=current_user["username"],
            duplicates_found=len(duplicates)
        )

        return response

    except Exception as e:
        logger.error(
            "Duplicate search failed",
            user=current_user["username"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search for duplicates"
        )


@router.post("/optimize")
async def optimize_code(
    code: str,
    optimization_level: str = "standard",
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Optimize and refactor test code
    """
    await rate_limiter.check_limit(f"optimize:code:{current_user['id']}")

    try:
        from app.services.optimization_service import OptimizationService

        optimization_service = OptimizationService()
        result = await optimization_service.optimize_code(
            code=code,
            level=optimization_level
        )

        logger.info(
            "Code optimization completed",
            user=current_user["username"],
            optimization_level=optimization_level,
            improvements_count=len(result["improvements"])
        )

        return result

    except Exception as e:
        logger.error(
            "Code optimization failed",
            user=current_user["username"],
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize code"
        )


@router.get("/metrics")
async def get_quality_metrics(
    project_id: int = None,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get quality metrics for tests
    """
    # TODO: Implement metrics collection
    return {
        "total_tests": 0,
        "pass_rate": 0.0,
        "coverage": 0.0,
        "duplicates": 0,
        "maintainability_index": 0.0
    }