import ast
import re
from typing import Any, Dict, List, Optional
import structlog

from app.core.logging import LoggerMixin

logger = structlog.get_logger(__name__)


class ValidationService(LoggerMixin):
    """Service for validating Python test code"""

    def __init__(self):
        self.required_decorators = {
            "allure": ["@allure.feature", "@allure.story", "@allure.title"],
            "pytest": ["def test_"],
            "general": []
        }

    async def validate_structure(
        self,
        code: str,
        standards: List[str] = None,
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Validate code structure against standards
        """
        standards = standards or ["allure"]
        errors = []
        warnings = []
        suggestions = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "errors": [{
                    "type": "SyntaxError",
                    "message": e.msg,
                    "line": e.lineno,
                    "column": e.offset
                }],
                "warnings": [],
                "suggestions": ["Fix syntax errors before validation"]
            }

        # Check each standard
        if "allure" in standards:
            allure_errors, allure_warnings, allure_suggestions = self._check_allure_structure(tree)
            errors.extend(allure_errors)
            warnings.extend(allure_warnings)
            suggestions.extend(allure_suggestions)

        # Check pytest structure
        pytest_errors, pytest_warnings, pytest_suggestions = self._check_pytest_structure(tree)
        errors.extend(pytest_errors)
        warnings.extend(pytest_warnings)
        suggestions.extend(pytest_suggestions)

        # Check AAA pattern
        aaa_errors, aaa_warnings, aaa_suggestions = self._check_aaa_pattern(tree, code)
        errors.extend(aaa_errors)
        warnings.extend(aaa_warnings)
        suggestions.extend(aaa_suggestions)

        # General code quality
        if strict_mode:
            quality_errors, quality_warnings, quality_suggestions = self._check_code_quality(tree, code)
            errors.extend(quality_errors)
            warnings.extend(quality_warnings)
            suggestions.extend(quality_suggestions)

        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    def _check_allure_structure(self, tree: ast.AST) -> tuple[List[Dict], List[Dict], List[str]]:
        """Check Allure decorator structure"""
        errors = []
        warnings = []
        suggestions = []

        required = self.required_decorators["allure"]

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                decorators = []
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Attribute):
                        decorator_name = f"{decorator.value.id}.{decorator.attr}"
                        decorators.append(decorator_name)

                missing_decorators = [dec for dec in required if dec not in decorators]
                if missing_decorators:
                    errors.append({
                        "type": "missing_decorator",
                        "message": f"Missing required decorators: {', '.join(missing_decorators)}",
                        "line": node.lineno,
                        "suggestion": f"Add: {', '.join(missing_decorators)}"
                    })

                # Check for @allure.manual if it's a manual test
                if "with allure.step" not in ast.get_source_segment(open(__file__).read(), node) or "":
                    warnings.append({
                        "type": "missing_steps",
                        "message": "Test function without allure.step decorators",
                        "line": node.lineno
                    })

        return errors, warnings, suggestions

    def _check_pytest_structure(self, tree: ast.AST) -> tuple[List[Dict], List[Dict], List[str]]:
        """Check pytest structure"""
        errors = []
        warnings = []
        suggestions = []

        test_functions = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("test_"):
                    test_functions += 1

                    # Check for assertions
                    has_assert = self._has_assert(node)
                    if not has_assert:
                        warnings.append({
                            "type": "no_assertions",
                            "message": f"Test function '{node.name}' has no assertions",
                            "line": node.lineno
                        })

        if test_functions == 0:
            errors.append({
                "type": "no_tests",
                "message": "No test functions found (functions starting with 'test_')"
            })

        return errors, warnings, suggestions

    def _check_aaa_pattern(self, tree: ast.AST, code: str) -> tuple[List[Dict], List[Dict], List[str]]:
        """Check Arrange-Act-Assert pattern"""
        errors = []
        warnings = []
        suggestions = []

        # Look for allure.step patterns
        step_pattern = r'with allure\.step\("([^"]+)"\)'
        steps = re.findall(step_pattern, code)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Check if function has AAA structure
                if not steps:
                    warnings.append({
                        "type": "no_aaa_structure",
                        "message": f"Test '{node.name}' doesn't follow AAA pattern with allure.step",
                        "line": node.lineno,
                        "suggestion": "Use with allure.step() for Arrange, Act, Assert phases"
                    })

        return errors, warnings, suggestions

    def _check_code_quality(self, tree: ast.AST, code: str) -> tuple[List[Dict], List[Dict], List[str]]:
        """Check general code quality"""
        errors = []
        warnings = []
        suggestions = []

        # Check function complexity
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    warnings.append({
                        "type": "high_complexity",
                        "message": f"Function '{node.name}' has high complexity ({complexity})",
                        "line": node.lineno,
                        "suggestion": "Consider breaking down into smaller functions"
                    })

        # Check for magic numbers
        magic_numbers = re.findall(r'\b\d+\b', code)
        if len(magic_numbers) > 5:
            warnings.append({
                "type": "magic_numbers",
                "message": f"Found {len(magic_numbers)} magic numbers in code",
                "suggestion": "Extract magic numbers to named constants"
            })

        return errors, warnings, suggestions

    def _has_assert(self, node: ast.FunctionDef) -> bool:
        """Check if function has assertions"""
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                return True
        return False

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
        return complexity

    def calculate_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate various code metrics"""
        try:
            tree = ast.parse(code)
        except:
            return {}

        metrics = {
            "lines_of_code": len(code.splitlines()),
            "functions": 0,
            "test_functions": 0,
            "assertions": 0,
            "allure_steps": 0,
            "decorators": 0
        }

        # Count allure steps
        metrics["allure_steps"] = len(re.findall(r'with allure\.step', code))

        # Count assertions
        metrics["assertions"] = len(re.findall(r'\bassert\b', code))

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics["functions"] += 1
                if node.name.startswith("test_"):
                    metrics["test_functions"] += 1
                metrics["decorators"] += len(node.decorator_list)

        return metrics