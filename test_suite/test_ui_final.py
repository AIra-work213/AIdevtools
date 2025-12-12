#!/usr/bin/env python3
"""
Итоговый тест для функции запуска сгенерированных UI тестов
Проверяет, что сгенерированные тесты могут выполняться в браузере
"""

import pytest
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/backend'))

from app.services.ai_service import AIService
from app.services.code_validator import CodeValidator
from app.core.logging import setup_logging

setup_logging()


class TestUIExecutionFinal:
    """Финальные тесты выполнения UI тестов"""

    @pytest.fixture
    def ai_service(self):
        return AIService()

    @pytest.fixture
    def validator(self):
        return CodeValidator(timeout=60)

    @pytest.mark.asyncio
    async def test_selenium_ui_execution_success(self, ai_service, validator):
        """Тест: сгенерированный Selenium тест должен успешно выполняться"""
        print("\n=== Тест выполнения Selenium UI теста ===")

        # Генерация теста
        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )

        assert result is not None
        assert "code" in result

        code = result["code"]
        print(f"✓ Код сгенерирован (длина: {len(code)})")

        # Проверка headless конфигурации
        assert "--headless" in code, "Отсутствует headless конфигурация"
        assert "--no-sandbox" in code, "Отсутствует no-sandbox"
        print("✓ Headless конфигурация корректна")

        # Валидация синтаксиса
        syntax_errors = validator.validate_syntax(code)
        assert len(syntax_errors) == 0, f"Синтаксические ошибки: {syntax_errors}"
        print("✓ Синтаксис корректен")

        # Выполнение
        execution = validator.execute_code(
            code=code,
            run_with_pytest=True
        )

        # Проверка результатов
        print(f"\nРезультаты выполнения:")
        print(f"  - Может выполняться: {execution.can_execute}")
        print(f"  - Ошибок выполнения: {len(execution.runtime_errors)}")

        # Детальная проверка Allure результатов
        if execution.allure_results:
            results = execution.allure_results
            print(f"\nДетальные результаты:")
            print(f"  - Всего тестов: {results.get('total_tests', 0)}")
            print(f"  - Прошло: {results.get('passed', 0)}")
            print(f"  - Сломано: {results.get('broken', 0)}")
            print(f"  - Провалено: {results.get('failed', 0)}")

            # Проверяем, что нет сломанных тестов
            assert results.get('broken', 0) == 0, f"Есть сломанные тесты: {results.get('broken', 0)}"

            # Проверяем, что есть пройденные тесты
            assert results.get('passed', 0) > 0, "Нет пройденных тестов"

        # Главная проверка
        assert execution.can_execute, "Тест должен быть выполнимым"
        assert len(execution.runtime_errors) == 0, "Не должно быть ошибок выполнения"

        print("\n✅ UI тест успешно выполнен в браузере!")

    @pytest.mark.asyncio
    async def test_playwright_ui_syntax_check(self, ai_service, validator):
        """Тест: Playwright тест должен иметь корректный синтаксис"""
        print("\n=== Тест синтаксиса Playwright UI теста ===")

        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="playwright"
        )

        code = result["code"]
        print(f"✓ Код сгенерирован")

        # Проверка синтаксиса
        syntax_errors = validator.validate_syntax(code)
        assert len(syntax_errors) == 0, f"Синтаксические ошибки: {syntax_errors}"
        print("✓ Синтаксис корректен")

        # Проверка наличия ключевых слов Playwright
        assert "playwright" in code.lower() or "page." in code, "Код не содержит Playwright"
        print("✓ Код содержит Playwright")

    @pytest.mark.asyncio
    async def test_html_ui_test_execution(self, ai_service, validator):
        """Тест: генерация из HTML должна работать"""
        print("\n=== Тест генерации из HTML ===")

        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Тестовая страница</title></head>
        <body>
            <h1>Заголовок</h1>
            <button id="btn1">Кнопка 1</button>
            <button id="btn2">Кнопка 2</button>
            <p>Текстовый параграф</p>
        </body>
        </html>
        """

        result = await ai_service.generate_ui_tests(
            input_method="html",
            html_content=html_content,
            framework="selenium"
        )

        code = result["code"]
        print(f"✓ Код сгенерирован из HTML")

        # Проверка синтаксиса
        syntax_errors = validator.validate_syntax(code)
        assert len(syntax_errors) == 0, f"Синтаксические ошибки: {syntax_errors}"
        print("✓ Синтаксис корректен")

        # Проверка элементов из HTML
        assert "Заголовок" in code or "h1" in code, "Тест не проверяет заголовок"
        assert "Кнопка" in code or "button" in code, "Тест не проверяет кнопки"
        print("✓ Тест проверяет элементы из HTML")

    def test_validator_handles_invalid_code(self, validator):
        """Тест: валидатор должен корректно обрабатывать невалидный код"""
        print("\n=== Тест обработки невалидного кода ===")

        invalid_code = '''
def test_invalid(
    print("нет закрывающей скобки")
'''

        syntax_errors = validator.validate_syntax(invalid_code)
        assert len(syntax_errors) > 0, "Должны быть синтаксические ошибки"
        print("✓ Синтаксические ошибки обнаружены")

        execution = validator.execute_code(
            code=invalid_code,
            run_with_pytest=False
        )

        assert not execution.can_execute, "Невалидный код не должен выполняться"
        print("✓ Невалидный код не выполняется")


def run_final_tests():
    """Запуск финальных тестов"""
    print("\n" + "="*60)
    print("  🧪 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ВЫПОЛНЕНИЯ UI ТЕСТОВ")
    print("="*60)

    pytest_args = [
        __file__,
        "-v",
        "-s",
        "--tb=short"
    ]

    exit_code = pytest.main(pytest_args)

    if exit_code == 0:
        print("\n" + "="*60)
        print("  🎉 ВСЕ ФИНАЛЬНЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("  ✓ Функция запуска UI тестов работает корректно")
        print("  ✓ Сгенерированные тесты выполняются в браузере")
        print("  ✓ Нет сломанных тестов (status Broken)")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("  ❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        print("  Требуется дополнительная отладка")
        print("="*60)

    return exit_code


if __name__ == "__main__":
    exit_code = run_final_tests()
    sys.exit(exit_code)