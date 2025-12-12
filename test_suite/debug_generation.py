#!/usr/bin/env python3
"""
Скрипт для отладки генерации UI тестов
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/backend'))

from app.services.ai_service import AIService
from app.core.logging import setup_logging

setup_logging()


async def main():
    ai_service = AIService()

    # Генерируем тест для example.com
    print("Генерация теста для example.com...")
    result = await ai_service.generate_ui_tests(
        input_method="url",
        url="https://example.com",
        framework="selenium"
    )

    # Сохраняем сгенерированный код
    with open("debug_generated_test.py", "w") as f:
        f.write(result["code"])

    print("Сгенерированный код сохранен в debug_generated_test.py")
    print(f"Длина кода: {len(result['code'])}")
    print("\nСценарии:")
    for scenario in result.get("test_scenarios", []):
        print(f"  - {scenario}")

    print("\nКод:")
    print(result["code"])


if __name__ == "__main__":
    asyncio.run(main())