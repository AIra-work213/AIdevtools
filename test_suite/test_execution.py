#!/usr/bin/env python3
"""
Тест выполнения сгенерированных UI тестов
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/backend'))

from app.services.ai_service import AIService
from app.services.code_validator import CodeValidator
from app.core.logging import setup_logging

setup_logging()


async def test_selenium_execution():
    """Тест выполнения Selenium тестов"""
    print("\n=== Тест выполнения Selenium теста ===")

    ai_service = AIService()
    validator = CodeValidator(timeout=60)

    # Генерируем тест
    result = await ai_service.generate_ui_tests(
        input_method="url",
        url="https://example.com",
        framework="selenium"
    )

    code = result["code"]
    print(f"✓ Код сгенерирован (длина: {len(code)})")

    # Валидация
    syntax_errors = validator.validate_syntax(code)
    print(f"✓ Синтаксических ошибок: {len(syntax_errors)}")
    assert len(syntax_errors) == 0, "Синтаксические ошибки!"

    # Выполнение
    print("Запуск теста...")
    execution = validator.execute_code(
        code=code,
        run_with_pytest=True
    )

    print(f"Результат:")
    print(f"  - Может выполняться: {execution.can_execute}")
    print(f"  - Ошибок выполнения: {len(execution.runtime_errors)}")

    if execution.allure_results:
        results = execution.allure_results
        print(f"  - Всего тестов: {results.get('total_tests', 0)}")
        print(f"  - Прошло: {results.get('passed', 0)}")
        print(f"  - Сломано: {results.get('broken', 0)}")
        print(f"  - Провалено: {results.get('failed', 0)}")

        if results.get('broken', 0) > 0:
            print(f"  ⚠️  Есть сломанные тесты!")
            return False

    # Вывод ошибок
    if execution.runtime_errors:
        print("\nОшибки:")
        for error in execution.runtime_errors[:3]:
            print(f"  - {error[:150]}")

    return execution.can_execute


async def main():
    print("🚀 Тестирование выполнения сгенерированных UI тестов\n")

    results = []

    # Selenium тест
    selenium_ok = await test_selenium_execution()
    results.append(("Selenium", selenium_ok))

    # Итоги
    print("\n\n" + "="*50)
    print("ИТОГИ:")
    for name, ok in results:
        status = "✅ OK" if ok else "❌ FAIL"
        print(f"  {name}: {status}")

    all_ok = all(ok for _, ok in results)

    if all_ok:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ!")
        return 0
    else:
        print("\n⚠️  Есть проблемы с выполнением тестов")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)