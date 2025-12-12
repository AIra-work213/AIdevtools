#!/usr/bin/env python3
"""
Скрипт для сохранения сгенерированного кода в файл для анализа
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/backend'))

from app.services.ai_service import AIService


async def save_generated_code():
    ai_service = AIService()
    
    # Генерация простого теста
    print("Генерация теста...")
    result = await ai_service.generate_ui_tests(
        input_method="url",
        url="https://example.com",
        framework="selenium"
    )
    
    code = result['code']
    
    # Сохранение в файл
    with open('generated_selenium_test.py', 'w') as f:
        f.write(code)
    
    print(f"✓ Код сохранен в generated_selenium_test.py ({len(code)} символов)")
    print("\nПервые 1000 символов:")
    print("=" * 80)
    print(code[:1000])
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(save_generated_code())
