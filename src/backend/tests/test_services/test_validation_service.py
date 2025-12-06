import pytest
from app.services.validation_service import ValidationService


class TestValidationService:
    """Test validation service"""

    def setup_method(self):
        """Setup validation service for each test"""
        self.validation_service = ValidationService()

    def test_validate_allure_code_success(self):
        """Test validation of correct Allure code"""
        valid_code = """
@allure.feature("Login")
@allure.story("Authentication")
@allure.title("User login test")
def test_user_login():
    with allure.step("Arrange: Setup data"):
        username = "testuser"
        password = "testpass"
    with allure.step("Act: Perform login"):
        result = login(username, password)
    with allure.step("Assert: Check result"):
        assert result.success is True
        """

        result = self.validation_service._check_allure_structure(
            self._parse_code(valid_code)
        )

        assert len(result[0]) == 0  # No errors

    def test_validate_missing_decorators(self):
        """Test validation of code missing required decorators"""
        invalid_code = """
def test_login():
    pass
        """

        result = self.validation_service._check_allure_structure(
            self._parse_code(invalid_code)
        )

        errors = result[0]
        assert len(errors) > 0
        assert any("Missing required decorators" in error["message"] for error in errors)

    def test_validate_no_assertions(self):
        """Test validation of code without assertions"""
        code_without_assert = """
@allure.feature("Login")
def test_login():
    print("This test has no assertions")
        """

        result = self.validation_service._check_pytest_structure(
            self._parse_code(code_without_assert)
        )

        warnings = result[1]
        assert len(warnings) > 0
        assert any("no assertions" in warning["message"] for warning in warnings)

    def test_validate_high_complexity(self):
        """Test validation detects high complexity"""
        complex_code = """
@allure.feature("Complex")
def test_complex():
    if condition1:
        if condition2:
            if condition3:
                if condition4:
                    if condition5:
                        if condition6:
                            if condition7:
                                pass
        """

        result = self.validation_service._check_code_quality(
            self._parse_code(complex_code),
            complex_code
        )

        warnings = result[1]
        assert len(warnings) > 0
        assert any("high complexity" in warning["message"] for warning in warnings)

    def test_calculate_metrics(self):
        """Test metrics calculation"""
        sample_code = """
@allure.feature("Test")
@allure.story("Metrics")
def test_metrics():
    with allure.step("Step 1"):
        data = prepare_data()
    with allure.step("Step 2"):
        result = process(data)
    with allure.step("Assert"):
        assert result is not None

def another_test():
    assert True
        """

        metrics = self.validation_service.calculate_metrics(sample_code)

        assert "lines_of_code" in metrics
        assert "functions" in metrics
        assert "test_functions" in metrics
        assert "assertions" in metrics
        assert "allure_steps" in metrics

        assert metrics["test_functions"] == 2
        assert metrics["assertions"] == 2
        assert metrics["allure_steps"] == 3

    def _parse_code(self, code: str):
        """Helper method to parse code to AST"""
        import ast
        return ast.parse(code)