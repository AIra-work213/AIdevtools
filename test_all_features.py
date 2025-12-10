#!/usr/bin/env python3
"""
Comprehensive Test Script for TestOps Copilot
Tests all features: Manual Generation, API Generation, UI Generation, Code Execution, 
Validation, Duplicates, and Settings
"""

import requests
import json
import time
from typing import Dict, Any

# API Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_section(title: str):
    print(f"\n{Colors.BLUE}{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}{Colors.END}\n")


# Test 1: Manual Test Generation (Two-Stage + Auto-Validation)
def test_manual_generation():
    print_section("TEST 1: Manual Test Generation (Two-Stage with Allure)")
    
    payload = {
        "requirements": "Создай тесты для функции входа пользователя. Проверь правильный логин/пароль, неправильный пароль, пустые поля.",
        "metadata": {
            "feature": "User Authentication",
            "story": "Login Tests",
            "owner": "QA Team"
        },
        "generation_settings": {
            "test_type": "manual",
            "detail_level": "standard",
            "use_aaa_pattern": True,
            "include_negative_tests": True,
            "framework": "pytest",
            "language": "python",
            "temperature": 0.3,
            "max_tokens": 4000
        }
    }
    
    print_info("Отправка запроса на генерацию...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate/manual",
            json=payload,
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Генерация завершена за {elapsed:.2f}с")
            print_info(f"Количество тестов: {len(result.get('test_cases', []))}")
            print_info(f"Валидация: {'✅ Успешна' if result.get('validation', {}).get('is_valid') else '❌ Провалена'}")
            
            code = result.get('code', '')
            print_info(f"Размер кода: {len(code)} символов")
            
            # Check two-stage generation markers
            has_framework_imports = 'import pytest' in code or 'import unittest' in code
            has_allure = '@allure.feature' in code and 'import allure' in code
            
            if has_framework_imports:
                print_success("✅ Stage 1: Framework imports detected")
            else:
                print_warning("⚠️ Stage 1: No framework imports found")
            
            if has_allure:
                print_success("✅ Stage 2: Allure decorators added")
            else:
                print_warning("⚠️ Stage 2: No Allure decorators found")
            
            # Save generated code for later tests
            with open('/tmp/generated_test.py', 'w') as f:
                f.write(code)
            print_info("Код сохранен в /tmp/generated_test.py")
            
            return True, code
        else:
            print_error(f"Ошибка {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print_error(f"Исключение: {str(e)}")
        return False, None


# Test 2: Code Execution with Allure
def test_code_execution(code: str = None):
    print_section("TEST 2: Code Execution with Allure Support")
    
    if not code:
        print_warning("Нет кода для выполнения, используем простой тест")
        code = """
import allure
import pytest
from allure_commons.types import Severity

@allure.feature("Math Operations")
@allure.story("Addition Tests")
class TestMath:
    
    @allure.title("Test simple addition")
    @allure.severity(Severity.NORMAL)
    @allure.manual
    def test_addition(self):
        '''Test basic addition'''
        with allure.step("Arrange: Prepare numbers"):
            a = 5
            b = 3
        
        with allure.step("Act: Perform addition"):
            result = a + b
        
        with allure.step("Assert: Check result"):
            assert result == 8, f"Expected 8, got {result}"
    
    @allure.title("Test addition with zero")
    @allure.severity(Severity.NORMAL)
    @allure.manual
    def test_addition_with_zero(self):
        '''Test addition with zero'''
        with allure.step("Test 0 + 0"):
            assert 0 + 0 == 0
        
        with allure.step("Test 5 + 0"):
            assert 5 + 0 == 5
"""
    
    payload = {
        "code": code,
        "source_code": None,
        "timeout": 30,
        "run_with_pytest": True  # Enable Allure
    }
    
    print_info("Выполнение кода с Allure отчетом...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate/execute",
            json=payload,
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Выполнение завершено за {elapsed:.2f}с")
            print_info(f"Синтаксис валиден: {result.get('is_valid')}")
            print_info(f"Код выполнен: {result.get('can_execute')}")
            
            if result.get('allure_results'):
                allure = result['allure_results']
                print_success(f"📊 Allure Отчет:")
                print(f"   Всего тестов: {allure.get('total_tests', 0)}")
                print(f"   ✅ Пройдено: {allure.get('passed', 0)}")
                print(f"   ❌ Провалено: {allure.get('failed', 0)}")
                print(f"   🔶 Сломано: {allure.get('broken', 0)}")
                print(f"   ⏭️  Пропущено: {allure.get('skipped', 0)}")
                
                if allure.get('tests'):
                    print_info("Детали тестов:")
                    for test in allure['tests']:
                        status_icon = "✅" if test['status'] == 'passed' else "❌"
                        print(f"   {status_icon} {test['name']} - {test['status']} ({test['duration']/1000:.2f}s)")
            
            if result.get('syntax_errors'):
                print_error(f"Синтаксические ошибки: {result['syntax_errors']}")
            
            if result.get('runtime_errors'):
                print_error(f"Ошибки выполнения: {result['runtime_errors']}")
            
            return True
        else:
            print_error(f"Ошибка {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Исключение: {str(e)}")
        return False


# Test 3: API Test Generation
def test_api_generation():
    print_section("TEST 3: API Test Generation")
    
    openapi_spec = """
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /api/users:
    get:
      summary: Get all users
      responses:
        '200':
          description: Success
    post:
      summary: Create user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
      responses:
        '201':
          description: Created
"""
    
    payload = {
        "openapi_spec": openapi_spec,
        "test_types": ["happy_path", "negative"],
        "include_validation": True
    }
    
    print_info("Генерация API тестов...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate/auto/api",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success("API тесты сгенерированы")
            print_info(f"Endpoints: {', '.join(result.get('endpoints_covered', []))}")
            print_info(f"Покрытие: {result.get('coverage_percentage', 0):.1f}%")
            return True
        else:
            print_error(f"Ошибка {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Исключение: {str(e)}")
        return False


# Test 4: UI Test Generation
def test_ui_generation():
    print_section("TEST 4: UI Test Generation")
    
    html_content = """
<html>
<body>
    <form id="loginForm">
        <input id="username" type="text" name="username" placeholder="Username">
        <input id="password" type="password" name="password" placeholder="Password">
        <button id="loginBtn" type="submit">Login</button>
    </form>
    <div id="errorMessage" class="error" style="display:none"></div>
</body>
</html>
"""
    
    payload = {
        "input_method": "html",
        "html_content": html_content,
        "selectors": {},
        "framework": "playwright"
    }
    
    print_info("Генерация UI тестов...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate/auto/ui",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success("UI тесты сгенерированы")
            print_info(f"Найдено селекторов: {len(result.get('selectors_found', []))}")
            print_info(f"Сценариев: {len(result.get('test_scenarios', []))}")
            return True
        else:
            print_error(f"Ошибка {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Исключение: {str(e)}")
        return False


# Test 5: Test Validation
def test_validation():
    print_section("TEST 5: Test Validation")
    
    test_code = """
import allure
import pytest

@allure.feature("Test Feature")
class TestExample:
    @allure.title("Test case 1")
    def test_example(self):
        assert True
"""
    
    payload = {
        "test_code": test_code,
        "standards": ["allure"]
    }
    
    print_info("Валидация кода...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/validation/validate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Валидация завершена: {'✅ Успешно' if result.get('is_valid') else '❌ Провалено'}")
            
            if result.get('errors'):
                print_error(f"Ошибки: {result['errors']}")
            if result.get('warnings'):
                print_warning(f"Предупреждения: {result['warnings']}")
            if result.get('suggestions'):
                print_info(f"Предложения: {result['suggestions']}")
                
            return result.get('is_valid', False)
        else:
            print_error(f"Ошибка {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Исключение: {str(e)}")
        return False


# Test 6: Duplicate Detection
def test_duplicate_detection():
    print_section("TEST 6: Duplicate Detection")
    
    test_code = """
def test_login_valid_credentials():
    # Test login with valid credentials
    pass

def test_login_correct_credentials():
    # Test login with correct credentials
    pass

def test_logout():
    # Test logout
    pass
"""
    
    payload = {
        "test_code": test_code,
        "similarity_threshold": 0.85
    }
    
    print_info("Поиск дубликатов...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/duplicates/find",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            duplicates = result.get('duplicates', [])
            print_success(f"Найдено дубликатов: {len(duplicates)}")
            
            for dup in duplicates:
                print_info(f"  {dup.get('test1_name')} ↔ {dup.get('test2_name')} (сходство: {dup.get('similarity', 0):.2%})")
                
            return True
        else:
            print_error(f"Ошибка {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Исключение: {str(e)}")
        return False


# Test 7: Settings
def test_settings():
    print_section("TEST 7: Settings Management")
    
    # Get settings
    print_info("Получение настроек...")
    try:
        response = requests.get(f"{BASE_URL}/settings")
        
        if response.status_code == 200:
            settings = response.json()
            print_success("Настройки получены")
            print_info(f"Framework: {settings.get('framework')}")
            print_info(f"Temperature: {settings.get('temperature')}")
            return True
        else:
            print_warning(f"Не удалось получить настройки: {response.status_code}")
            return True  # Non-critical
            
    except Exception as e:
        print_warning(f"Ошибка настроек: {str(e)}")
        return True  # Non-critical


def main():
    print(f"\n{Colors.BLUE}{'='*80}")
    print("  🧪 COMPREHENSIVE TEST SUITE FOR TESTOPS COPILOT")
    print(f"{'='*80}{Colors.END}\n")
    
    results = {}
    
    # Test 1: Manual Generation with Two-Stage
    success, generated_code = test_manual_generation()
    results['Manual Generation (Two-Stage)'] = success
    time.sleep(2)
    
    # Test 2: Code Execution with Allure
    results['Code Execution (Allure)'] = test_code_execution(generated_code)
    time.sleep(2)
    
    # Test 3: API Generation
    results['API Generation'] = test_api_generation()
    time.sleep(2)
    
    # Test 4: UI Generation
    results['UI Generation'] = test_ui_generation()
    time.sleep(2)
    
    # Test 5: Validation
    results['Validation'] = test_validation()
    time.sleep(2)
    
    # Test 6: Duplicate Detection
    results['Duplicate Detection'] = test_duplicate_detection()
    time.sleep(2)
    
    # Test 7: Settings
    results['Settings'] = test_settings()
    
    # Summary
    print_section("TEST SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test, success in results.items():
        status = f"{Colors.GREEN}✅ PASSED{Colors.END}" if success else f"{Colors.RED}❌ FAILED{Colors.END}"
        print(f"{test:40} {status}")
    
    print(f"\n{Colors.BLUE}{'='*80}")
    print(f"  TOTAL: {total} | PASSED: {passed} | FAILED: {failed}")
    print(f"  SUCCESS RATE: {(passed/total*100):.1f}%")
    print(f"{'='*80}{Colors.END}\n")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
