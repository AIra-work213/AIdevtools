#!/usr/bin/env python3
"""
Тест всех поддерживаемых UI фреймворков
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


async def test_framework(framework: str, url: str = "https://example.com"):
    """Тест конкретного фреймворка"""
    print(f"\n{'='*20} Тест {framework.upper()} {'='*20}")

    ai_service = AIService()
    validator = CodeValidator(timeout=30)

    # Генерация
    print(f"\n[1/3] Генерация {framework} теста...")
    result = await ai_service.generate_ui_tests(
        input_method="url",
        url=url,
        framework=framework
    )

    code = result["code"]
    print(f"✓ Код сгенерирован ({len(code)} символов)")

    # Показываем первые строки кода
    lines = code.split('\n')[:15]
    print("\nСгенерированный код (первые 15 строк):")
    print("-" * 50)
    for line in lines:
        print(line)
    print("-" * 50)
    print("...")

    # Валидация синтаксиса
    print("\n[2/3] Проверка синтаксиса...")
    syntax_errors = validator.validate_syntax(code)
    print(f"✓ Синтаксических ошибок: {len(syntax_errors)}")

    if syntax_errors:
        print("\nОшибки синтаксиса:")
        for error in syntax_errors[:3]:
            print(f"  - {error}")
        return False

    # Попытка выполнения
    print("\n[3/3] Проверка выполнения...")

    # Для Cypress не запускаем (требуется Node.js)
    if framework == "cypress":
        print("⚠️  Cypress требует Node.js окружения, выполняем только синтаксическую проверку")
        # Проверяем наличие ключевых слов
        assert "describe" in code or "it(" in code, "Отсутствуют Cypress тестовые функции"
        assert "cy." in code, "Отсутствуют Cypress команды"
        print("✓ Код содержит Cypress специфичные элементы")
    else:
        # Для Python фреймворков пытаемся выполнить
        execution = validator.execute_code(
            code=code,
            run_with_pytest=False  # Без pytest для упрощения
        )

        print(f"  - Может выполняться: {execution.can_execute}")

        if execution.runtime_errors:
            print(f"\nОшибки выполнения:")
            for error in execution.runtime_errors[:3]:
                print(f"  - {error[:100]}")

    return True


async def test_html_with_frameworks():
    """Тест генерации из HTML для разных фреймворков"""
    print(f"\n{'='*20} Тест из HTML {'='*20}")

    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Форма входа</title></head>
    <body>
        <form id="loginForm">
            <input type="text" id="username" placeholder="Логин">
            <input type="password" id="password" placeholder="Пароль">
            <button type="submit" id="submitBtn">Войти</button>
            <a href="/register" id="registerLink">Регистрация</a>
        </form>
    </body>
    </html>
    """

    frameworks = ["playwright", "selenium", "cypress"]
    results = {}

    for framework in frameworks:
        print(f"\nГенерация {framework} из HTML...")

        ai_service = AIService()
        result = await ai_service.generate_ui_tests(
            input_method="html",
            html_content=html_content,
            framework=framework,
            selectors={
                "form": "#loginForm",
                "username": "#username",
                "password": "#password",
                "submit": "#submitBtn",
                "register": "#registerLink"
            }
        )

        code = result["code"]
        print(f"✓ Длина кода: {len(code)}")

        # Проверяем наличие элементов
        has_form = any(s in code.lower() for s in ["loginform", "form", "username"])
        has_inputs = any(s in code.lower() for s in ["username", "password"])
        has_button = "submit" in code.lower() or "кнопку" in code.lower()

        results[framework] = {
            "code_length": len(code),
            "has_form": has_form,
            "has_inputs": has_inputs,
            "has_button": has_button
        }

        print(f"  - Проверяет форму: {'✓' if has_form else '✗'}")
        print(f"  - Проверяет инпуты: {'✓' if has_inputs else '✗'}")
        print(f"  - Проверяет кнопку: {'✓' if has_button else '✗'}")

    return results


async def main():
    print("🚀 Тестирование всех поддерживаемых UI фреймворков\n")

    # Тестируем каждый фреймворк
    frameworks = ["playwright", "selenium", "cypress"]
    results = {}

    for framework in frameworks:
        success = await test_framework(framework)
        results[framework] = success

    # Тест из HTML
    html_results = await test_html_with_frameworks()

    # Итоги
    print("\n\n" + "="*60)
    print("  📊 ИТОГИ ТЕСТИРОВАНИЯ ФРЕЙМВОРКОВ")
    print("="*60)

    print("\nГенерация из URL:")
    for framework, success in results.items():
        status = "✅ OK" if success else "❌ FAIL"
        print(f"  {framework.capitalize():12} - {status}")

    print("\nГенерация из HTML:")
    for framework, checks in html_results.items():
        passed = sum(checks.values())
        total = len(checks)
        status = "✅" if passed == total else "⚠️"
        print(f"  {framework.capitalize():12} - {status} ({passed}/{total} проверок)")

    print("\nПоддерживаемые фреймворки:")
    print("  1. 🎭 Playwright - Python, автоматизация браузеров")
    print("  2. 🔧 Selenium - Python, классическая автоматизация")
    print("  3. 🌳 Cypress - JavaScript, современные E2E тесты")

    print("\nРекомендации:")
    print("  - Для Python проектов: Playwright (современный) или Selenium (классический)")
    print("  - Для JavaScript/TypeScript: Cypress")
    print("  - Playwright лучше поддерживает современные веб-стандарты")
    print("  - Selenium имеет большую экосистему и документацию")


if __name__ == "__main__":
    asyncio.run(main())