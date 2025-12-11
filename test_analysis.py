#!/usr/bin/env python3
"""
Проверка анализа страницы
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

    # Анализируем структуру сайта
    print("Анализ сайта example.com...")
    result = await ai_service._analyze_website_structure("https://example.com")

    print("\nРезультат анализа:")
    print(f"  - Найдено URL: {result['discovered_urls']}")
    print(f"  - Структура: {result['structure']}")

    # Теперь генерируем тест с отладкой
    print("\n\nГенерация теста...")
    gen_result = await ai_service.generate_ui_tests(
        input_method="url",
        url="https://example.com",
        framework="selenium"
    )

    # Сохраняем код
    with open("debug_test.py", "w") as f:
        f.write(gen_result['code'])

    print("\nСгенерированный код сохранен в debug_test.py")
    print(f"Длина: {len(gen_result['code'])}")


if __name__ == "__main__":
    asyncio.run(main())