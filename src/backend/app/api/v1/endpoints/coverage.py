"""API endpoints for code coverage analysis"""

from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog

from app.schemas.test import (
    UploadedFile,
    CoverageAnalysisRequest,
    CoverageAnalysisResponse,
    GenerateTestsForCoverageRequest,
    GenerateTestsForCoverageResponse,
    ValidationResult
)
from app.services.coverage_service import coverage_service, uploader_service
from app.services.ai_service import ai_service
from app.services.validation_service import validation_service

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/analyze", response_model=CoverageAnalysisResponse)
async def analyze_coverage(
    files: List[UploadFile] = File(...),
    language: str = Form(default="python"),
    framework: str = Form(default="pytest"),
    include_suggestions: bool = Form(default=True)
):
    """
    Analyze code coverage for uploaded files
    """
    try:
        uploaded_files = []
        test_files = []

        # Process uploaded files
        for file in files:
            content = await file.read()
            is_test = "test" in file.filename.lower() or "spec" in file.filename.lower()

            uploaded_file = await uploader_service.upload_from_file(
                content, file.filename, is_test
            )

            if is_test:
                test_files.append(uploaded_file)
            else:
                uploaded_files.append(uploaded_file)

        # Create analysis request
        request = CoverageAnalysisRequest(
            project_files=uploaded_files,
            test_files=test_files,
            language=language,
            framework=framework,
            include_suggestions=include_suggestions
        )

        # Perform coverage analysis
        result = await coverage_service.analyze_coverage(request)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/github")
async def upload_from_github(
    repo_url: str = Form(...),
    language: str = Form(default="python"),
    framework: str = Form(default="pytest")
):
    """
    Upload and analyze code from GitHub repository
    """
    try:
        logger.info("Starting GitHub upload", repo_url=repo_url, language=language, framework=framework)
        
        # Download repository
        files = await uploader_service.upload_from_github(repo_url)
        logger.info("Repository uploaded", file_count=len(files))

        # Separate test files
        source_files = [f for f in files if not f.is_test_file]
        test_files = [f for f in files if f.is_test_file]
        logger.info("Files separated", source_files=len(source_files), test_files=len(test_files))

        # Create analysis request
        request = CoverageAnalysisRequest(
            project_files=source_files,
            test_files=test_files,
            language=language,
            framework=framework,
            include_suggestions=True
        )

        logger.info("Starting coverage analysis")
        # Perform coverage analysis
        result = await coverage_service.analyze_coverage(request)
        logger.info("Coverage analysis complete", overall_coverage=result.overall_coverage)

        return result

    except Exception as e:
        logger.error("Failed to process GitHub repository", 
                    repo_url=repo_url, 
                    error=str(e), 
                    error_type=type(e).__name__,
                    exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process GitHub repository: {str(e)}")


@router.post("/upload/gitlab")
async def upload_from_gitlab(
    repo_url: str = Form(...),
    language: str = Form(default="python"),
    framework: str = Form(default="pytest")
):
    """
    Upload and analyze code from GitLab repository
    """
    try:
        # Download repository
        files = await uploader_service.upload_from_gitlab(repo_url)

        # Separate test files
        source_files = [f for f in files if not f.is_test_file]
        test_files = [f for f in files if f.is_test_file]

        # Create analysis request
        request = CoverageAnalysisRequest(
            project_files=source_files,
            test_files=test_files,
            language=language,
            framework=framework,
            include_suggestions=True
        )

        # Perform coverage analysis
        result = await coverage_service.analyze_coverage(request)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process GitLab repository: {str(e)}")


@router.post("/generate-tests", response_model=GenerateTestsForCoverageResponse)
async def generate_tests_for_coverage(
    request: GenerateTestsForCoverageRequest
):
    """
    Generate tests to improve coverage for uncovered functions
    """
    try:
        logger.info("Starting test generation", 
                   function_count=len(request.uncovered_functions),
                   language=request.generation_settings.language if request.generation_settings else "python",
                   framework=request.generation_settings.framework if request.generation_settings else "pytest")
        
        generated_tests = {}
        total_improvement = 0
        all_errors = []
        all_warnings = []
        all_suggestions = []

        # Generate tests for each uncovered function
        for i, func in enumerate(request.uncovered_functions):
            logger.info(f"Generating test {i+1}/{len(request.uncovered_functions)}", 
                       function_name=func.name, 
                       file_path=func.file_path,
                       complexity=func.complexity)
            # Create prompt for AI
            system_prompt = f"""You are an expert test engineer. Generate comprehensive unit tests using {request.generation_settings.framework if request.generation_settings else 'pytest'} framework.

Requirements:
1. Follow AAA pattern (Arrange-Act-Assert)
2. Include both positive and negative test cases
3. Test all branches and edge cases
4. Use descriptive test names
5. Include proper assertions
6. Return ONLY the test code without explanations"""

            user_prompt = f"""Generate unit tests for this function:

Function: {func.name}
File: {func.file_path}
Lines: {func.line_start}-{func.line_end}
Signature: {func.signature}
Complexity: {func.complexity}
Priority: {func.priority}

Project Context:
{request.project_context}
"""

            # Generate test code using generate_code method
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            test_code = await ai_service.generate_code(
                messages=messages,
                max_tokens=request.generation_settings.max_tokens if request.generation_settings else 2000,
                temperature=request.generation_settings.temperature if request.generation_settings else 0.3
            )

            # Validate generated test
            validation_result = await validation_service.validate_structure(
                code=test_code,
                standards=["pytest"],
                strict_mode=False
            )
            
            # Collect validation results
            if validation_result.get("errors"):
                all_errors.extend(validation_result["errors"])
                logger.warning(f"Validation errors for {func.name}", 
                             errors=validation_result["errors"])
            
            if validation_result.get("warnings"):
                all_warnings.extend(validation_result["warnings"])
            
            if validation_result.get("suggestions"):
                all_suggestions.extend(validation_result["suggestions"])

            # Store generated test even if there are warnings (but not errors)
            if not validation_result.get("errors"):
                generated_tests[func.name] = test_code
                # Estimate coverage improvement (simplified)
                estimated_improvement = 1.0 / (func.complexity + 1)
                total_improvement += estimated_improvement
                
                logger.info(f"Test generated and validated successfully", 
                           function_name=func.name,
                           code_length=len(test_code),
                           warnings_count=len(validation_result.get("warnings", [])))
            else:
                logger.error(f"Test validation failed for {func.name}", 
                           errors=validation_result["errors"])

        # Calculate validation result
        is_valid = len(all_errors) == 0
        coverage_improvement = min(total_improvement * 100, 100)  # Cap at 100%

        # Determine test files created
        test_files_created = [f"test_{name}.py" for name in generated_tests.keys()]

        logger.info("Test generation complete", 
                   tests_generated=len(generated_tests),
                   coverage_improvement=coverage_improvement,
                   errors_count=len(all_errors),
                   warnings_count=len(all_warnings),
                   suggestions_count=len(all_suggestions))

        return GenerateTestsForCoverageResponse(
            generated_tests=generated_tests,
            coverage_improvement=coverage_improvement,
            validation=ValidationResult(
                is_valid=is_valid,
                errors=all_errors,
                warnings=all_warnings,
                suggestions=all_suggestions
            ),
            test_files_created=test_files_created
        )

    except Exception as e:
        logger.error("Failed to generate tests", 
                    error=str(e), 
                    error_type=type(e).__name__,
                    exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate tests: {str(e)}")


@router.get("/supported-languages")
async def get_supported_languages():
    """
    Get list of supported programming languages for coverage analysis
    """
    return {
        "languages": [
            {
                "name": "Python",
                "value": "python",
                "frameworks": ["pytest", "unittest"]
            },
            {
                "name": "JavaScript",
                "value": "javascript",
                "frameworks": ["jest", "mocha"]
            },
            {
                "name": "TypeScript",
                "value": "typescript",
                "frameworks": ["jest", "vitest"]
            },
            {
                "name": "Java",
                "value": "java",
                "frameworks": ["junit", "testng"]
            },
            {
                "name": "C#",
                "value": "csharp",
                "frameworks": ["nunit", "xunit"]
            }
        ]
    }


@router.post("/export")
async def export_coverage_report(
    request: CoverageAnalysisRequest,
    format: str = Form(default="json")  # json, html, pdf
):
    """
    Export coverage report in different formats
    """
    try:
        # Perform analysis
        result = await coverage_service.analyze_coverage(request)

        if format == "json":
            return result

        elif format == "html":
            # Generate HTML report
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Code Coverage Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                    .coverage-high {{ color: green; }}
                    .coverage-medium {{ color: orange; }}
                    .coverage-low {{ color: red; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Code Coverage Report</h1>
                    <p>Overall Coverage: <strong class="coverage-{'high' if result.overall_coverage >= 80 else 'medium' if result.overall_coverage >= 50 else 'low'}">{result.overall_coverage:.1f}%</strong></p>
                    <p>Source Files: {result.total_files}</p>
                    <p>Test Files: {result.test_files}</p>
                </div>

                <h2>File Coverage</h2>
                <table>
                    <tr>
                        <th>File</th>
                        <th>Functions</th>
                        <th>Coverage</th>
                    </tr>
            """

            for file_path, metrics in result.file_coverage.items():
                coverage_class = 'high' if metrics.coverage_percentage >= 80 else 'medium' if metrics.coverage_percentage >= 50 else 'low'
                html_content += f"""
                    <tr>
                        <td>{file_path}</td>
                        <td>{metrics.functions_covered}/{metrics.functions_total}</td>
                        <td class="coverage-{coverage_class}">{metrics.coverage_percentage:.1f}%</td>
                    </tr>
                """

            html_content += """
                </table>

                <h2>Uncovered Functions</h2>
                <ul>
            """

            for func in result.uncovered_functions[:10]:
                html_content += f"""
                    <li>
                        <strong>{func.name}</strong>
                        <span class="coverage-{func.priority}">[{func.priority}]</span>
                        <br>
                        <small>{func.file_path}:{func.line_start}</small>
                    </li>
                """

            html_content += """
                </ul>
            </body>
            </html>
            """

            return JSONResponse(
                content=html_content,
                headers={"Content-Disposition": "attachment; filename=coverage_report.html"}
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))