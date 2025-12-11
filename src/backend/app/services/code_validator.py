"""
Code Validator Service
Validates and executes generated test code with Allure support
"""
import ast
import subprocess
import tempfile
import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import structlog

logger = structlog.get_logger()


class CodeValidationResult:
    def __init__(
        self,
        is_valid: bool,
        can_execute: bool,
        syntax_errors: List[str],
        runtime_errors: List[str],
        execution_output: Optional[str] = None,
        execution_time: Optional[float] = None,
        allure_report_path: Optional[str] = None,
        allure_results: Optional[Dict[str, Any]] = None,
    ):
        self.is_valid = is_valid
        self.can_execute = can_execute
        self.syntax_errors = syntax_errors
        self.runtime_errors = runtime_errors
        self.execution_output = execution_output
        self.execution_time = execution_time
        self.allure_report_path = allure_report_path
        self.allure_results = allure_results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "can_execute": self.can_execute,
            "syntax_errors": self.syntax_errors,
            "runtime_errors": self.runtime_errors,
            "execution_output": self.execution_output,
            "execution_time": self.execution_time,
            "allure_report_path": self.allure_report_path,
            "allure_results": self.allure_results,
        }


class CodeValidator:
    """Validates and executes Python code with Allure support"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.allure_results_dir = Path(tempfile.gettempdir()) / "allure-results"

    def validate_syntax(self, code: str) -> List[str]:
        """Validate Python syntax"""
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")
        return errors

    def has_allure_decorators(self, code: str) -> bool:
        """Check if code contains Allure decorators"""
        allure_patterns = [
            "@allure.feature",
            "@allure.story",
            "@allure.title",
            "import allure",
            "allure.step"
        ]
        return any(pattern in code for pattern in allure_patterns)

    def execute_code(
        self, 
        code: str, 
        source_code: Optional[str] = None,
        run_with_pytest: bool = False
    ) -> CodeValidationResult:
        """
        Execute Python code in isolated environment
        
        Args:
            code: Test code to execute
            source_code: Optional source code that tests depend on
            run_with_pytest: If True, run with pytest (enables Allure)
        """
        import time
        
        # First validate syntax
        syntax_errors = self.validate_syntax(code)
        if syntax_errors:
            return CodeValidationResult(
                is_valid=False,
                can_execute=False,
                syntax_errors=syntax_errors,
                runtime_errors=[],
            )

        # Detect if code has Allure decorators
        has_allure = self.has_allure_decorators(code)
        if has_allure:
            run_with_pytest = True  # Force pytest if Allure is detected

        # Combine source code and test code if provided
        full_code = code
        if source_code:
            full_code = f"{source_code}\n\n{code}"

        # Prepare Allure results directory
        allure_results_path = None
        allure_results = None
        
        if run_with_pytest:
            # Create unique results directory
            import uuid
            run_id = uuid.uuid4().hex[:8]
            allure_results_path = self.allure_results_dir / run_id
            allure_results_path.mkdir(parents=True, exist_ok=True)

        # Create temporary file for execution
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(full_code)
            temp_file = f.name

        runtime_errors = []
        execution_output = ""
        full_output = ""
        execution_time = 0.0

        try:
            start_time = time.time()
            
            if run_with_pytest:
                # Execute with pytest and Allure
                cmd = [
                    "python3", "-m", "pytest",
                    temp_file,
                    "-v",
                    f"--alluredir={allure_results_path}",
                    "--tb=long",
                    "-p", "no:warnings"  # Suppress warnings for cleaner output
                ]
                
                logger.info("Running pytest with Allure", allure_dir=str(allure_results_path))
            else:
                # Execute code directly
                cmd = ["python3", temp_file]
            
            # Propagate env and hint browser locations for Selenium/Playwright
            env = os.environ.copy()
            env.setdefault("CHROME_BIN", "/usr/bin/chromium")
            env.setdefault("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
            # Execute code in subprocess for isolation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
            )
            
            execution_time = time.time() - start_time
            execution_output = result.stdout
            
            # Combine stdout and stderr for better error visibility
            if result.stderr:
                full_output = f"{execution_output}\n\nSTDERR:\n{result.stderr}"
            else:
                full_output = execution_output

            if result.returncode != 0:
                # Pytest return codes:
                # 0: All tests passed
                # 1: Tests failed
                # 2: No tests collected or internal error
                # 3: Internal error
                # 4: pytest command line usage error
                # 5: No tests collected
                
                if result.returncode == 2:
                    runtime_errors.append("pytest: No tests collected. Tests may have syntax errors or missing dependencies.")
                elif result.returncode == 5:
                    runtime_errors.append("pytest: No tests found in file.")
                else:
                    runtime_errors.append(f"pytest exit code {result.returncode}")
                
                # Surface whatever output we have (stdout/stderr) to help debug
                runtime_errors.append(full_output or result.stderr or execution_output)
                can_execute = False
                
                logger.warning(
                    "Code execution failed",
                    return_code=result.returncode,
                    stderr_length=len(result.stderr),
                    stdout_length=len(result.stdout),
                    sample_output=full_output[:10000]
                )
            else:
                can_execute = True

            # Parse Allure results if available
            if run_with_pytest and allure_results_path and allure_results_path.exists():
                allure_results = self._parse_allure_results(allure_results_path)

            logger.info(
                "Code execution completed",
                return_code=result.returncode,
                execution_time=execution_time,
                with_pytest=run_with_pytest,
                has_allure=has_allure
            )

        except subprocess.TimeoutExpired:
            runtime_errors.append(f"Execution timeout ({self.timeout}s)")
            can_execute = False
        except Exception as e:
            runtime_errors.append(f"Execution error: {str(e)}")
            can_execute = False
        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_file)
            except:
                pass

        return CodeValidationResult(
            is_valid=len(syntax_errors) == 0,
            can_execute=can_execute,
            syntax_errors=syntax_errors,
            runtime_errors=runtime_errors,
            execution_output=full_output if run_with_pytest else execution_output,
            execution_time=execution_time,
            allure_report_path=str(allure_results_path) if allure_results_path else None,
            allure_results=allure_results,
        )

    def _parse_allure_results(self, results_dir: Path) -> Dict[str, Any]:
        """Parse Allure JSON results"""
        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "broken": 0,
            "skipped": 0,
            "tests": []
        }

        try:
            # Find all result JSON files
            result_files = list(results_dir.glob("*-result.json"))
            
            for result_file in result_files:
                with open(result_file, 'r') as f:
                    test_result = json.load(f)
                    
                    results["total_tests"] += 1
                    status = test_result.get("status", "unknown")
                    
                    if status == "passed":
                        results["passed"] += 1
                    elif status == "failed":
                        results["failed"] += 1
                    elif status == "broken":
                        results["broken"] += 1
                    elif status == "skipped":
                        results["skipped"] += 1
                    
                    results["tests"].append({
                        "name": test_result.get("name", "Unknown"),
                        "status": status,
                        "duration": test_result.get("stop", 0) - test_result.get("start", 0),
                        "fullName": test_result.get("fullName", "")
                    })

            logger.info("Parsed Allure results", results=results)
            
        except Exception as e:
            logger.error("Failed to parse Allure results", error=str(e))

        return results

    def validate_and_fix(self, code: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Validate code and attempt to fix common issues
        
        Args:
            code: Code to validate and fix
            max_retries: Maximum number of fix attempts
        
        Returns:
            Dict with fixed_code, is_valid, fixes_applied, remaining_errors
        """
        fixes_applied = []
        fixed_code = code
        
        for attempt in range(max_retries):
            # Check syntax
            syntax_errors = self.validate_syntax(fixed_code)
            
            if not syntax_errors:
                return {
                    "fixed_code": fixed_code,
                    "is_valid": True,
                    "fixes_applied": fixes_applied,
                    "remaining_errors": [],
                }
            
            # Try to fix common issues
            if attempt < max_retries - 1:  # Don't fix on last attempt
                fixed_code, new_fixes = self._apply_common_fixes(fixed_code, syntax_errors)
                fixes_applied.extend(new_fixes)
                
                if not new_fixes:
                    # No fixes were applied, stop trying
                    break

        # Final validation
        final_errors = self.validate_syntax(fixed_code)

        return {
            "fixed_code": fixed_code,
            "is_valid": len(final_errors) == 0,
            "fixes_applied": fixes_applied,
            "remaining_errors": final_errors,
        }

    def _apply_common_fixes(self, code: str, errors: List[str]) -> Tuple[str, List[str]]:
        """Apply common fixes to code based on errors"""
        fixes = []
        fixed_code = code

        # Fix missing imports
        if "pytest" in code and "import pytest" not in code:
            fixed_code = "import pytest\n" + fixed_code
            fixes.append("Added missing 'import pytest'")

        if "unittest" in code and "import unittest" not in code:
            fixed_code = "import unittest\n" + fixed_code
            fixes.append("Added missing 'import unittest'")

        if "@allure" in code and "import allure" not in code:
            fixed_code = "import allure\n" + fixed_code
            fixes.append("Added missing 'import allure'")

        if "Severity" in code and "from allure_commons.types import Severity" not in code:
            lines = fixed_code.split('\n')
            # Add after allure import
            for i, line in enumerate(lines):
                if 'import allure' in line:
                    lines.insert(i + 1, 'from allure_commons.types import Severity')
                    break
            fixed_code = '\n'.join(lines)
            fixes.append("Added missing 'from allure_commons.types import Severity'")

        # Fix indentation issues (basic)
        if any("IndentationError" in err or "expected an indented block" in err for err in errors):
            # Try to fix common indentation issues
            lines = fixed_code.split('\n')
            fixed_lines = []
            for i, line in enumerate(lines):
                # If line ends with : and next line is not indented, add 4 spaces
                if line.strip().endswith(':') and i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() and not next_line.startswith((' ', '\t')):
                        fixed_lines.append(line)
                        fixed_lines.append('    ' + next_line)
                        continue
                fixed_lines.append(line)
            
            if len(fixed_lines) != len(lines):
                fixed_code = '\n'.join(fixed_lines)
                fixes.append("Fixed indentation issues")

        return fixed_code, fixes

    async def validate_with_ai_retry(
        self, 
        code: str, 
        ai_service, 
        original_requirements: str,
        max_retries: int = 4
    ) -> Dict[str, Any]:
        """
        Validate code and use AI to fix if validation fails
        
        Args:
            code: Code to validate
            ai_service: AIService instance for code regeneration
            original_requirements: Original requirements for context
            max_retries: Maximum AI retry attempts
        
        Returns:
            Dict with final_code, is_valid, retries_count, validation_result
        """
        current_code = code
        retries_count = 0
        
        for retry in range(max_retries + 1):
            # Validate current code
            result = self.execute_code(current_code, run_with_pytest=True)
            
            if result.is_valid and result.can_execute:
                logger.info("Code validation successful", retries=retries_count)
                return {
                    "final_code": current_code,
                    "is_valid": True,
                    "retries_count": retries_count,
                    "validation_result": result.to_dict()
                }
            
            # If this was the last retry, return failure
            if retry >= max_retries:
                logger.warning("Code validation failed after max retries", retries=retries_count)
                return {
                    "final_code": current_code,
                    "is_valid": False,
                    "retries_count": retries_count,
                    "validation_result": result.to_dict()
                }
            
            # Try basic fixes first
            fix_result = self.validate_and_fix(current_code)
            if fix_result["is_valid"]:
                current_code = fix_result["fixed_code"]
                logger.info("Code fixed with basic fixes", fixes=fix_result["fixes_applied"])
                continue
            
            # Use AI to fix the code
            logger.info("Attempting AI-based code fix", retry=retry + 1)
            retries_count += 1
            
            # Build error context for AI
            error_context = self._build_error_context(result)
            
            # Ask AI to fix the code
            fix_prompt = f"""The following code has errors. Please fix them.

Original requirements:
{original_requirements}

Current code with errors:
```python
{current_code}
```

Errors found:
{error_context}

Please provide the corrected code that:
1. Fixes all syntax errors
2. Fixes all runtime errors
3. Ensures all tests can execute
4. Maintains all Allure decorators
5. Keeps the same test logic

Return ONLY the fixed Python code, no explanations."""

            try:
                # Use AI to generate fixed code
                fixed_code = await ai_service.llm_client.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are an expert Python developer fixing test code."},
                        {"role": "user", "content": fix_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=8000
                )
                
                # Clean markdown
                if isinstance(fixed_code, str):
                    if "```python" in fixed_code:
                        fixed_code = fixed_code.split("```python")[1].split("```")[0].strip()
                    elif "```" in fixed_code:
                        fixed_code = fixed_code.split("```")[1].split("```")[0].strip()
                
                current_code = fixed_code
                logger.info("AI fix applied", retry=retry + 1)
                
            except Exception as e:
                logger.error("AI fix failed", error=str(e))
                # Continue with current code
        
        # Should not reach here
        return {
            "final_code": current_code,
            "is_valid": False,
            "retries_count": retries_count,
            "validation_result": result.to_dict()
        }

    def _build_error_context(self, result: CodeValidationResult) -> str:
        """Build human-readable error context"""
        errors = []
        
        if result.syntax_errors:
            errors.append("Syntax Errors:")
            for err in result.syntax_errors:
                errors.append(f"  - {err}")
        
        if result.runtime_errors:
            errors.append("\nRuntime Errors:")
            for err in result.runtime_errors:
                errors.append(f"  - {err}")
        
        return "\n".join(errors) if errors else "No specific errors found"


# Singleton instance
_validator_instance = None


def get_code_validator() -> CodeValidator:
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CodeValidator()
    return _validator_instance
