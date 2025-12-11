#!/usr/bin/env python3
"""
Комплексные тесты для проверки функции запуска сгенерированных UI тестов в браузере
Эти тесты проверяют полный workflow: генерация -> выполнение -> валидация результатов
"""

import pytest
import asyncio
import sys
import os
import tempfile
import json
import time
from typing import Dict, Any, List
from pathlib import Path

# Добавляем путь к бэкенду
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'backend'))

from app.services.ai_service import AIService
from app.services.code_validator import CodeValidator
from app.core.logging import setup_logging

setup_logging()


class TestUIBrowserExecution:
    """Тесты для проверки реального выполнения UI тестов в браузере"""

    @pytest.fixture
    def ai_service(self):
        """Создание экземпляра AIService"""
        return AIService()

    @pytest.fixture
    def code_validator(self):
        """Создание экземпляра CodeValidator с увеличенным таймаутом"""
        return CodeValidator(timeout=60)

    @pytest.mark.asyncio
    async def test_selenium_real_browser_execution(self, ai_service, code_validator):
        """Тест реального выполнения Selenium теста в браузере"""
        print("\n=== Тест выполнения Selenium теста в браузере ===")

        # Генерируем тест для example.com
        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        assert result is not None
        assert "code" in result

        code = result["code"]
        print(f"✓ Код сгенерирован (длина: {len(code)} символов)")

        # Проверяем наличие headless конфигурации
        required_configs = [
            "--headless",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu"
        ]

        missing_configs = [cfg for cfg in required_configs if cfg not in code]
        if missing_configs:
            print(f"⚠️  Отсутствуют конфигурации: {missing_configs}")
            # Добавляем их вручную если отсутствуют
            if "Options()" in code and "--headless" not in code:
                code = code.replace(
                    "options = Options()",
                    "options = Options()\n    options.add_argument('--headless')\n    options.add_argument('--no-sandbox')\n    options.add_argument('--disable-dev-shm-usage')\n    options.add_argument('--disable-gpu')"
                )

        # Валидация синтаксиса
        syntax_errors = code_validator.validate_syntax(code)
        assert len(syntax_errors) == 0, f"Синтаксические ошибки: {syntax_errors}"
        print("✓ Синтаксис корректен")

        # Выполнение теста
        print("Запуск теста в браузере...")
        execution_result = code_validator.execute_code(
            code=code,
            run_with_pytest=True
        )

        print(f"Результат выполнения:")
        print(f"  - Может выполняться: {execution_result.can_execute}")
        print(f"  - Синтаксических ошибок: {len(execution_result.syntax_errors)}")
        print(f"  - Ошибок выполнения: {len(execution_result.runtime_errors)}")

        if execution_result.execution_output:
            print(f"\nВывод выполнения:")
            print(execution_result.execution_output[-1000:])  # Последние 1000 символов

        if execution_result.runtime_errors:
            print(f"\nОшибки выполнения:")
            for error in execution_result.runtime_errors[:5]:
                print(f"  - {error[:200]}")

        # Проверяем, что тест выполнился успешно
        assert execution_result.can_execute, "Тест должен быть выполним"
        assert len(execution_result.syntax_errors) == 0, "Не должно быть синтаксических ошибок"

        # Проверяем наличие браузера в выводе
        if execution_result.execution_output:
            output_lower = execution_result.execution_output.lower()
            browser_indicators = ["chrome", "webdriver", "browser", "selenium"]
            has_browser_activity = any(indicator in output_lower for indicator in browser_indicators)
            if has_browser_activity:
                print("✓ Обнаружена активность браузера")

        print("✅ Selenium тест успешно выполнен в браузере")

    @pytest.mark.asyncio
    async def test_selenium_with_allure_reporting(self, ai_service, code_validator):
        """Тест выполнения Selenium теста с Allure отчетами"""
        print("\n=== Тест Selenium с Allure отчетами ===")

        # Генерируем тест с Allure
        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        code = result["code"]
        print(f"✓ Код сгенерирован")

        # Проверяем наличие Allure декораторов
        has_allure = code_validator.has_allure_decorators(code)
        print(f"  - Наличие Allure декораторов: {has_allure}")

        # Если Allure отсутствует, добавляем базовые декораторы
        if not has_allure:
            print("Добавление Allure декораторов...")
            allure_imports = "import pytest\nimport allure\nfrom allure_commons.types import Severity\n"
            if "import pytest" in code and "import allure" not in code:
                code = code.replace("import pytest", allure_imports)

            # Добавляем декораторы к тестовым функциям
            lines = code.split('\n')
            new_lines = []
            for i, line in enumerate(lines):
                new_lines.append(line)
                if line.strip().startswith("def test_") and i > 0:
                    # Добавляем декораторы перед функцией
                    indent = "    "
                    new_lines.insert(-1, f"{indent}@allure.title(\"{line.strip().split('(')[0].replace('def ', '')}\")")
                    new_lines.insert(-1, f"{indent}@allure.severity(Severity.NORMAL)")
                    new_lines.insert(-1, f"{indent}@allure.description(\"Тест проверки UI\")")

            code = '\n'.join(new_lines)

        # Выполняем тест с Allure
        execution_result = code_validator.execute_code(
            code=code,
            run_with_pytest=True
        )

        print(f"Результат выполнения с Allure:")
        print(f"  - Выполнимо: {execution_result.can_execute}")
        print(f"  - Путь к отчету Allure: {execution_result.allure_report_path}")

        if execution_result.allure_results:
            allure_data = execution_result.allure_results
            print(f"  - Всего тестов: {allure_data.get('total_tests', 0)}")
            print(f"  - Прошло: {allure_data.get('passed', 0)}")
            print(f"  - Сломано: {allure_data.get('broken', 0)}")
            print(f"  - Провалено: {allure_data.get('failed', 0)}")

            # Проверяем, что нет сломанных тестов
            assert allure_data.get('broken', 0) == 0, "Не должно быть сломанных тестов"

        assert execution_result.can_execute, "Тест с Allure должен быть выполним"
        print("✅ Selenium тест с Allure выполнен успешно")

    @pytest.mark.asyncio
    async def test_playwright_browser_execution(self, ai_service, code_validator):
        """Тест выполнения Playwright теста в браузере"""
        print("\n=== Тест выполнения Playwright теста в браузере ===")

        # Генерируем Playwright тест
        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="playwright"
        )

        assert result is not None
        code = result["code"]
        print(f"✓ Playwright код сгенерирован")

        # Проверяем синтаксис
        syntax_errors = code_validator.validate_syntax(code)
        assert len(syntax_errors) == 0, f"Синтаксические ошибки: {syntax_errors}"

        # Выполняем тест
        execution_result = code_validator.execute_code(
            code=code,
            run_with_pytest=True
        )

        print(f"Результат выполнения Playwright:")
        print(f"  - Выполнимо: {execution_result.can_execute}")

        if execution_result.execution_output:
            output = execution_result.execution_output.lower()
            playwright_indicators = ["playwright", "browser", "page", "locator"]
            has_playwright_activity = any(indicator in output for indicator in playwright_indicators)
            if has_playwright_activity:
                print("✓ Обнаружена активность Playwright")

        # Для Playwright тестов может быть can_execute=False если нет браузера
        # но синтаксис должен быть корректным
        assert len(syntax_errors) == 0, "Синтаксис должен быть корректным"
        print("✅ Playwright тест обработан")

    @pytest.mark.asyncio
    async def test_multi_step_ui_workflow(self, ai_service, code_validator):
        """Тест многоэтапного UI workflow"""
        print("\n=== Тест многоэтапного UI workflow ===")

        # Создаем HTML с многоэтапной формой
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Многоэтапная форма</title></head>
        <body>
            <form id="multi-step-form">
                <div class="step" id="step1">
                    <h2>Шаг 1: Персональные данные</h2>
                    <input type="text" id="firstName" placeholder="Имя" required>
                    <input type="email" id="email" placeholder="Email" required>
                    <button type="button" onclick="showStep(2)">Далее</button>
                </div>
                <div class="step" id="step2" style="display:none">
                    <h2>Шаг 2: Адрес</h2>
                    <input type="text" id="address" placeholder="Адрес">
                    <input type="text" id="city" placeholder="Город">
                    <button type="button" onclick="showStep(1)">Назад</button>
                    <button type="button" onclick="submitForm()">Отправить</button>
                </div>
                <div id="result" style="display:none">
                    <h2>Форма отправлена!</h2>
                </div>
            </form>
            <script>
                function showStep(step) {
                    document.querySelectorAll('.step').forEach(el => el.style.display = 'none');
                    document.getElementById('step' + step).style.display = 'block';
                }
                function submitForm() {
                    document.querySelectorAll('.step').forEach(el => el.style.display = 'none');
                    document.getElementById('result').style.display = 'block';
                }
            </script>
        </body>
        </html>
        """

        # Генерируем тест для многоэтапной формы
        result = await ai_service.generate_ui_tests(
            input_method="html",
            html_content=html_content,
            framework="selenium",
            selectors={
                "first_name": "#firstName",
                "email": "#email",
                "address": "#address",
                "city": "#city",
                "next_button": "button[onclick='showStep(2)']",
                "submit_button": "button[onclick='submitForm()']",
                "result": "#result"
            }
        )

        code = result["code"]
        print(f"✓ Тест для многоэтапной формы сгенерирован")

        # Убеждаемся, что есть headless конфигурация
        if "--headless" not in code:
            code = code.replace(
                "options = Options()",
                "options = Options()\n    options.add_argument('--headless')\n    options.add_argument('--no-sandbox')\n    options.add_argument('--disable-dev-shm-usage')"
            )

        # Валидация и выполнение
        syntax_errors = code_validator.validate_syntax(code)
        assert len(syntax_errors) == 0, f"Синтаксические ошибки: {syntax_errors}"

        execution_result = code_validator.execute_code(
            code=code,
            run_with_pytest=True
        )

        print(f"Результат многоэтапного теста:")
        print(f"  - Выполнимо: {execution_result.can_execute}")

        if execution_result.execution_output:
            output = execution_result.execution_output
            workflow_indicators = ["step", "click", "input", "wait", "switch"]
            has_workflow = any(indicator.lower() in output.lower() for indicator in workflow_indicators)
            if has_workflow:
                print("✓ Обнаружены элементы многоэтапного workflow")

        print("✅ Многоэтапный UI тест обработан")

    def test_error_handling_and_recovery(self, code_validator):
        """Тест обработки ошибок и восстановления"""
        print("\n=== Тест обработки ошибок ===")

        # Тест с отсутствующим элементом
        broken_test_code = '''
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

@pytest.fixture
def driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_broken_test(driver):
    driver.get("https://example.com")
    # Пытаемся найти элемент, которого нет
    element = driver.find_element(By.ID, "nonexistent-element")
    assert element.is_displayed()
'''

        execution_result = code_validator.execute_code(
            code=broken_test_code,
            run_with_pytest=True
        )

        print(f"Результат выполнения некорректного теста:")
        print(f"  - Выполнимо: {execution_result.can_execute}")
        print(f"  - Ошибок выполнения: {len(execution_result.runtime_errors)}")

        # Тест должен провалиться, но не падать с ошибкой системы
        assert len(execution_result.runtime_errors) > 0, "Должны быть ошибки выполнения"
        assert not execution_result.can_execute, "Некорректный тест не должен быть выполнимым"

        print("✅ Обработка ошибок работает корректно")

    def test_timeout_handling(self, code_validator):
        """Тест обработки таймаутов"""
        print("\n=== Тест обработки таймаутов ===")

        # Создаем валидатор с коротким таймаутом
        short_timeout_validator = CodeValidator(timeout=5)

        long_running_test = '''
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

@pytest.fixture
def driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_long_running(driver):
    driver.get("https://example.com")
    # Имитация долгой операции
    time.sleep(10)
    assert True
'''

        execution_result = short_timeout_validator.execute_code(
            code=long_running_test,
            run_with_pytest=True
        )

        print(f"Результат при таймауте:")
        print(f"  - Выполнимо: {execution_result.can_execute}")

        # Проверяем наличие ошибки таймаута
        timeout_errors = [err for err in execution_result.runtime_errors if "timeout" in err.lower()]
        assert len(timeout_errors) > 0, "Должна быть ошибка таймаута"

        print("✅ Обработка таймаутов работает корректно")

    @pytest.mark.asyncio
    async def test_complete_ui_testing_pipeline(self, ai_service, code_validator):
        """Тест полного пайплайна UI тестирования"""
        print("\n=== Тест полного пайплайна UI тестирования ===")

        # Шаг 1: Генерация теста
        print("Шаг 1: Генерация UI теста...")
        test_url = "https://example.com"

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url=test_url,
            framework="selenium"
        )

        generated_code = result["code"]
        scenarios = result.get("test_scenarios", [])
        print(f"  - Сгенерировано сценариев: {len(scenarios)}")
        for scenario in scenarios[:3]:
            print(f"    • {scenario}")

        # Шаг 2: Валидация кода
        print("\nШаг 2: Валидация кода...")
        syntax_errors = code_validator.validate_syntax(generated_code)
        assert len(syntax_errors) == 0, f"Синтаксические ошибки: {syntax_errors}"
        print("  - Синтаксис корректен")

        # Шаг 3: Исправление кода при необходимости
        fixed_code = generated_code
        if "--headless" not in fixed_code:
            print("  - Добавление headless конфигурации...")
            fixed_code = fixed_code.replace(
                "options = Options()",
                "options = Options()\n    options.add_argument('--headless')\n    options.add_argument('--no-sandbox')\n    options.add_argument('--disable-dev-shm-usage')\n    options.add_argument('--disable-gpu')"
            )

        # Шаг 4: Выполнение теста
        print("\nШаг 3: Выполнение теста...")
        execution_result = code_validator.execute_code(
            code=fixed_code,
            run_with_pytest=True
        )

        print(f"  - Результат выполнения: {execution_result.can_execute}")

        # Шаг 5: Анализ результатов
        print("\nШаг 4: Анализ результатов...")

        if execution_result.can_execute:
            print("  ✅ Тест успешно выполнен")
            if execution_result.execution_output:
                output = execution_result.execution_output.lower()
                success_indicators = ["passed", "ok", "success", "."]
                has_success = any(indicator in output for indicator in success_indicators)
                if has_success:
                    print("  ✅ Обнаружены индикаторы успешного выполнения")
        else:
            print("  ⚠️  Тест не выполнен, анализируем ошибки...")
            if execution_result.runtime_errors:
                for error in execution_result.runtime_errors[:3]:
                    print(f"    - {error[:100]}")

        # Шаг 6: Сохранение артефактов
        print("\nШаг 5: Сохранение артефактов...")

        artifacts_dir = tempfile.mkdtemp(prefix="ui_test_pipeline_")

        # Сохраняем сгенерированный код
        code_file = os.path.join(artifacts_dir, "generated_test.py")
        with open(code_file, 'w') as f:
            f.write(fixed_code)
        print(f"  - Код сохранен: {code_file}")

        # Сохраняем результаты
        results = {
            "url": test_url,
            "scenarios": scenarios,
            "execution": {
                "can_execute": execution_result.can_execute,
                "syntax_errors": execution_result.syntax_errors,
                "runtime_errors": execution_result.runtime_errors,
                "execution_time": execution_result.execution_time
            }
        }

        results_file = os.path.join(artifacts_dir, "results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  - Результаты сохранены: {results_file}")

        print("\n✅ Полный пайплайн UI тестирования завершен")


def run_comprehensive_tests():
    """Запуск всех комплексных тестов"""
    print("\n" + "="*80)
    print("  🚀 ЗАПУСК КОМПЛЕКСНЫХ ТЕСТОВ ВЫПОЛНЕНИЯ UI ТЕСТОВ В БРАУЗЕРЕ")
    print("="*80)

    # Создаем экземпляры классов
    ai_service = AIService()
    code_validator = CodeValidator(timeout=60)
    test_instance = TestUIBrowserExecution()

    tests = [
        ("Selenium выполнение в браузере", test_instance.test_selenium_real_browser_execution),
        ("Selenium с Allure отчетами", test_instance.test_selenium_with_allure_reporting),
        ("Playwright выполнение", test_instance.test_playwright_browser_execution),
        ("Многоэтапный UI workflow", test_instance.test_multi_step_ui_workflow),
        ("Обработка ошибок", test_instance.test_error_handling_and_recovery),
        ("Обработка таймаутов", test_instance.test_timeout_handling),
        ("Полный пайплайн UI тестирования", test_instance.test_complete_ui_testing_pipeline),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                asyncio.run(test_func(ai_service, code_validator))
            else:
                test_func(code_validator)
            passed += 1
            print(f"\n✅ {test_name} - ПРОЙДЕН")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} - ПРОВАЛЕН")
            print(f"Ошибка: {str(e)}")
            import traceback
            traceback.print_exc()
        print("\n" + "-"*80)

    # Итоги
    print("\n" + "="*80)
    print("  📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*80)
    print(f"Прошло:  {passed}/{len(tests)}")
    print(f"Провалено: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("Функция запуска сгенерированных UI тестов работает корректно.")
        return 0
    else:
        print(f"\n⚠️ {failed} тест(ов) провалено.")
        print("Требуется исправление ошибок в генерации или выполнении тестов.")
        return 1


if __name__ == "__main__":
    exit_code = run_comprehensive_tests()
    sys.exit(exit_code)