#!/usr/bin/env python3
"""
Скрипт для реальной проверки генерации и выполнения UI-тестов
Проверяет весь workflow: генерация -> валидация -> выполнение
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


async def test_selenium_generation_and_execution():
    """Тест генерации и выполнения Selenium теста"""
    print("=" * 80)
    print("ТЕСТ 1: Генерация и выполнение простого Selenium теста")
    print("=" * 80)
    
    ai_service = AIService()
    validator = CodeValidator(timeout=30)
    
    try:
        # Генерация теста
        print("\n[1/4] Генерация UI теста для example.com...")
        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com",
            framework="selenium"
        )
        
        print(f"✓ Тест сгенерирован, длина: {len(result['code'])} символов")
        print(f"\nСгенерированный код (первые 500 символов):")
        print("-" * 80)
        print(result['code'][:500])
        print("-" * 80)
        
        # Проверка наличия headless конфигурации
        print("\n[2/4] Проверка headless конфигурации...")
        code = result['code']
        has_headless = '--headless' in code
        has_no_sandbox = '--no-sandbox' in code
        has_disable_dev_shm = '--disable-dev-shm-usage' in code
        
        print(f"  - --headless: {'✓' if has_headless else '✗'}")
        print(f"  - --no-sandbox: {'✓' if has_no_sandbox else '✗'}")
        print(f"  - --disable-dev-shm-usage: {'✓' if has_disable_dev_shm else '✗'}")
        
        if not (has_headless and has_no_sandbox):
            print("\n⚠️  ПРЕДУПРЕЖДЕНИЕ: Отсутствует критичная headless конфигурация!")
        
        # Валидация синтаксиса
        print("\n[3/4] Валидация синтаксиса...")
        syntax_errors = validator.validate_syntax(code)
        
        if syntax_errors:
            print(f"✗ Найдены ошибки синтаксиса:")
            for error in syntax_errors:
                print(f"  - {error}")
            return False
        else:
            print("✓ Синтаксис корректен")
        
        # Выполнение
        print("\n[4/4] Выполнение теста...")
        execution_result = validator.execute_code(
            code=code,
            run_with_pytest=True
        )
        
        print(f"\nРезультат выполнения:")
        print(f"  - can_execute: {execution_result.can_execute}")
        print(f"  - Ошибки выполнения: {len(execution_result.runtime_errors)}")
        
        if execution_result.execution_output:
            print(f"\nВывод выполнения (последние 1000 символов):")
            print("-" * 80)
            print(execution_result.execution_output[-1000:])
            print("-" * 80)
        
        if execution_result.runtime_errors:
            print(f"\nОшибки:")
            for error in execution_result.runtime_errors[:5]:  # Первые 5 ошибок
                print(f"  - {error[:200]}")
        
        if execution_result.can_execute:
            print("\n✅ ТЕСТ ПРОШЕЛ УСПЕШНО!")
            return True
        else:
            print("\n❌ ТЕСТ ПРОВАЛИЛСЯ")
            return False
            
    except Exception as e:
        print(f"\n❌ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_selenium_with_allure():
    """Тест генерации Selenium с Allure декораторами"""
    print("\n\n" + "=" * 80)
    print("ТЕСТ 2: Генерация Selenium теста с Allure декораторами")
    print("=" * 80)
    
    ai_service = AIService()
    validator = CodeValidator(timeout=30)
    
    try:
        # Генерация (должна быть 2 этапа: base + allure)
        print("\n[1/4] Генерация UI теста с Allure...")
        result = await ai_service.generate_ui_tests(
            input_method="url",
            url="https://example.com/login",
            framework="selenium"
        )
        
        code = result['code']
        print(f"✓ Тест сгенерирован, длина: {len(code)} символов")
        
        # Проверка наличия Allure
        print("\n[2/4] Проверка Allure декораторов...")
        has_allure = validator.has_allure_decorators(code)
        
        if has_allure:
            print("✓ Найдены Allure декораторы")
            # Детальная проверка
            checks = {
                "import allure": "import allure" in code,
                "@allure.": "@allure." in code,
                "allure.step": "allure.step" in code
            }
            for check, found in checks.items():
                print(f"  - {check}: {'✓' if found else '✗'}")
        else:
            print("✗ Allure декораторы не найдены (Stage 2 не сработал)")
        
        # Валидация
        print("\n[3/4] Валидация синтаксиса...")
        syntax_errors = validator.validate_syntax(code)
        
        if syntax_errors:
            print(f"✗ Ошибки: {syntax_errors}")
            return False
        else:
            print("✓ Синтаксис корректен")
        
        # Выполнение
        print("\n[4/4] Выполнение теста с Allure...")
        execution_result = validator.execute_code(
            code=code,
            run_with_pytest=True
        )
        
        print(f"\nРезультат:")
        print(f"  - can_execute: {execution_result.can_execute}")
        print(f"  - allure_report_path: {execution_result.allure_report_path}")
        
        if execution_result.runtime_errors:
            print(f"\nОшибки:")
            for error in execution_result.runtime_errors[:3]:
                print(f"  - {error[:200]}")
        
        if execution_result.can_execute:
            print("\n✅ ТЕСТ С ALLURE ПРОШЕЛ!")
            return True
        else:
            print("\n❌ ТЕСТ С ALLURE ПРОВАЛИЛСЯ")
            return False
            
    except Exception as e:
        print(f"\n❌ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Запуск всех тестов"""
    print("🚀 Запуск интеграционных тестов UI генерации и выполнения\n")
    
    results = []
    
    # Тест 1: Базовый Selenium
    result1 = await test_selenium_generation_and_execution()
    results.append(("Базовый Selenium тест", result1))
    
    # Тест 2: Selenium с Allure
    result2 = await test_selenium_with_allure()
    results.append(("Selenium с Allure", result2))
    
    # Итоговая сводка
    print("\n\n" + "=" * 80)
    print("ИТОГОВАЯ СВОДКА")
    print("=" * 80)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        return 0
    else:
        print("\n⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛИЛИСЬ")
        failed = [name for name, result in results if not result]
        print(f"Провалившиеся тесты: {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
