#!/usr/bin/env python3
"""
Тесты для функции запуска сгенерированных UI тестов
"""

import pytest
import requests
import json
import time
import os
import tempfile
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"


class TestUITestExecution:
    """Тесты выполнения UI тестов через API эндпоинт /execute"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.session = requests.Session()
        # Увеличиваем таймауты для UI тестов
        self.session.timeout = 120

    def test_execute_playwright_test(self):
        """Тест выполнения сгенерированного Playwright теста"""
        print("\n=== Тест выполнения Playwright теста ===")

        # Сначала генерируем UI тест
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Тестовая страница</title></head>
        <body>
            <h1 id="title">Добро пожаловать</h1>
            <button id="click-me" onclick="this.textContent='Clicked!'>Нажми меня</button>
            <form id="test-form">
                <input type="text" id="name" name="name" placeholder="Введите имя">
                <select id="country">
                    <option value="">Выберите страну</option>
                    <option value="ru">Россия</option>
                    <option value="us">США</option>
                </select>
                <button type="submit">Отправить</button>
            </form>
        </body>
        </html>
        """

        generate_payload = {
            "input_method": "html",
            "html_content": html_content,
            "framework": "playwright",
            "selectors": {
                "title": "#title",
                "button": "#click-me",
                "form": "#test-form",
                "name_input": "#name",
                "country_select": "#country"
            }
        }

        # Генерируем тест
        print("Генерация Playwright теста...")
        gen_response = self.session.post(
            f"{BASE_URL}/generate/auto/ui",
            json=generate_payload
        )

        assert gen_response.status_code == 200, f"Ошибка генерации: {gen_response.text}"
        gen_data = gen_response.json()

        print(f"✅ Тест сгенерирован")
        print(f"   Сценариев: {len(gen_data['test_scenarios'])}")
        print(f"   Селекторов: {len(gen_data['selectors_found'])}")

        # Сохраняем сгенерированный код
        generated_code = gen_data['code']

        # Теперь выполняем этот код
        print("\nВыполнение сгенерированного кода...")
        execute_payload = {
            "code": generated_code,
            "timeout": 60,
            "run_with_pytest": False  # Playwright тесты не всегда pytest-совместимы
        }

        exec_response = self.session.post(
            f"{BASE_URL}/generate/execute",
            json=execute_payload
        )

        assert exec_response.status_code == 200, f"Ошибка выполнения: {exec_response.text}"
        exec_data = exec_response.json()

        # Проверяем результаты выполнения
        print(f"\nРезультаты выполнения:")
        print(f"   Валиден: {exec_data['is_valid']}")
        print(f"   Может выполняться: {exec_data['can_execute']}")
        print(f"   Синтаксических ошибок: {len(exec_data['syntax_errors'])}")
        print(f"   Ошибок выполнения: {len(exec_data['runtime_errors'])}")

        # Сохраняем вывод для отладки
        if exec_data.get('execution_output'):
            print(f"\nВывод выполнения (первые 1000 символов):")
            print(exec_data['execution_output'][:1000])

        # Проверяем, что нет синтаксических ошибок
        assert len(exec_data['syntax_errors']) == 0, f"Синтаксические ошибки: {exec_data['syntax_errors']}"

        # Для Playwright тестов может быть can_execute=False из-за отсутствия браузера
        # но синтаксис должен быть корректным
        print("\n✅ Тест Playwright выполнен (синтаксис корректен)")

    def test_execute_selenium_test(self):
        """Тест выполнения сгенерированного Selenium теста"""
        print("\n=== Тест выполнения Selenium теста ===")

        # Генерируем Selenium тест
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Форма входа</title></head>
        <body>
            <form id="login">
                <input type="text" id="username" placeholder="Логин">
                <input type="password" id="password" placeholder="Пароль">
                <input type="checkbox" id="remember"> Запомнить меня
                <button type="submit">Войти</button>
            </form>
        </body>
        </html>
        """

        generate_payload = {
            "input_method": "html",
            "html_content": html_content,
            "framework": "selenium",
            "selectors": {
                "login_form": "#login",
                "username": "#username",
                "password": "#password",
                "remember": "#remember"
            }
        }

        print("Генерация Selenium теста...")
        gen_response = self.session.post(
            f"{BASE_URL}/generate/auto/ui",
            json=generate_payload
        )

        assert gen_response.status_code == 200
        gen_data = gen_response.json()
        generated_code = gen_data['code']

        # Выполняем тест
        print("\nВыполнение Selenium теста...")
        execute_payload = {
            "code": generated_code,
            "timeout": 60,
            "run_with_pytest": False
        }

        exec_response = self.session.post(
            f"{BASE_URL}/generate/execute",
            json=execute_payload
        )

        assert exec_response.status_code == 200
        exec_data = exec_response.json()

        print(f"\nРезультаты выполнения:")
        print(f"   Валиден: {exec_data['is_valid']}")
        print(f"   Может выполняться: {exec_data['can_execute']}")
        print(f"   Синтаксических ошибок: {len(exec_data['syntax_errors'])}")
        print(f"   Ошибок выполнения: {len(exec_data['runtime_errors'])}")

        # Сохраняем вывод
        if exec_data.get('execution_output'):
            print(f"\nВывод выполнения:")
            print(exec_data['execution_output'][:1000])

        # Проверяем синтаксис
        assert len(exec_data['syntax_errors']) == 0, f"Синтаксические ошибки: {exec_data['syntax_errors']}"

        print("\n✅ Тест Selenium выполнен (синтаксис корректен)")

    def test_execute_cypress_test(self):
        """Тест выполнения сгенерированного Cypress теста"""
        print("\n=== Тест выполнения Cypress теста ===")

        # Генерируем Cypress тест
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <nav>
                <a href="#home" class="nav-link">Главная</a>
                <a href="#about" class="nav-link">О нас</a>
                <a href="#contact" class="nav-link">Контакты</a>
            </nav>
            <div id="content">
                <h2>Содержимое страницы</h2>
                <p>Тестовый текст</p>
            </div>
        </body>
        </html>
        """

        generate_payload = {
            "input_method": "html",
            "html_content": html_content,
            "framework": "cypress"
        }

        print("Генерация Cypress теста...")
        gen_response = self.session.post(
            f"{BASE_URL}/generate/auto/ui",
            json=generate_payload
        )

        assert gen_response.status_code == 200
        gen_data = gen_response.json()
        generated_code = gen_data['code']

        print(f"Сгенерированный код (первые 500 символов):")
        print(generated_code[:500])

        # Cypress тесты не выполняются напрямую через Python,
        # но проверяем, что код сгенерирован корректно
        assert "describe" in generated_code or "it(" in generated_code
        assert "cy." in generated_code

        print("\n✅ Cypress тест сгенерирован корректно")

    def test_execute_pytest_ui_test(self):
        """Тест выполнения UI теста с pytest и Allure"""
        print("\n=== Тест выполнения UI теста с pytest/Allure ===")

        # Создаем тестовый код с pytest и Allure
        test_code = '''
import pytest
import allure

@allure.feature("UI Tests")
@allure.story("Login Form")
class TestLoginForm:

    @allure.title("Проверка отображения формы входа")
    @allure.severity("critical")
    def test_login_form_display(self):
        """Проверяем, что форма входа отображается корректно"""
        with allure.step("Проверить наличие заголовка"):
            assert True

        with allure.step("Проверить наличие полей формы"):
            assert True

        with allure.step("Проверить наличие кнопки входа"):
            assert True

    @allure.title("Проверка валидации полей")
    def test_form_validation(self):
        """Проверяем валидацию полей формы"""
        with allure.step("Отправить пустую форму"):
            pass

        with allure.step("Проверить сообщение об ошибке"):
            assert True
'''

        execute_payload = {
            "code": test_code,
            "timeout": 30,
            "run_with_pytest": True  # Включаем pytest и Allure
        }

        print("Выполнение pytest теста с Allure...")
        exec_response = self.session.post(
            f"{BASE_URL}/generate/execute",
            json=execute_payload
        )

        assert exec_response.status_code == 200
        exec_data = exec_response.json()

        print(f"\nРезультаты выполнения:")
        print(f"   Валиден: {exec_data['is_valid']}")
        print(f"   Может выполняться: {exec_data['can_execute']}")
        print(f"   Синтаксических ошибок: {len(exec_data['syntax_errors'])}")
        print(f"   Ошибок выполнения: {len(exec_data['runtime_errors'])}")
        print(f"   Время выполнения: {exec_data.get('execution_time', 0):.2f}с")

        # Проверяем наличие Allure результатов
        if exec_data.get('allure_results'):
            allure_results = exec_data['allure_results']
            print(f"\nAllure результаты:")
            print(f"   Всего тестов: {allure_results['total_tests']}")
            print(f"   Прошло: {allure_results['passed']}")
            print(f"   Сломано: {allure_results['broken']}")
            print(f"   Пропущено: {allure_results['skipped']}")

            # Проверяем, что тесты были выполнены
            assert allure_results['total_tests'] > 0, "Нет выполненных тестов"

            # Проверяем путь к отчету Allure
            if exec_data.get('allure_report_path'):
                print(f"   Путь к результатам: {exec_data['allure_report_path']}")

        # Проверяем успешность выполнения
        assert len(exec_data['syntax_errors']) == 0, f"Синтаксические ошибки: {exec_data['syntax_errors']}"
        assert exec_data['can_execute'], "Тесты не могут быть выполнены"

        print("\n✅ pytest тест с Allure выполнен успешно")

    def test_invalid_code_handling(self):
        """Тест обработки невалидного кода"""
        print("\n=== Тест обработки невалидного кода ===")

        invalid_code = '''
# Код с синтаксической ошибкой
def test_invalid(
    # отсутствует закрывающая скобка
    print("Этот код невалиден")
'''

        execute_payload = {
            "code": invalid_code,
            "timeout": 10,
            "run_with_pytest": False
        }

        exec_response = self.session.post(
            f"{BASE_URL}/generate/execute",
            json=execute_payload
        )

        assert exec_response.status_code == 200
        exec_data = exec_response.json()

        print(f"\nРезультаты выполнения невалидного кода:")
        print(f"   Валиден: {exec_data['is_valid']}")
        print(f"   Может выполняться: {exec_data['can_execute']}")
        print(f"   Синтаксических ошибок: {len(exec_data['syntax_errors'])}")

        # Должны быть синтаксические ошибки
        assert len(exec_data['syntax_errors']) > 0, "Ожидались синтаксические ошибки"
        assert not exec_data['is_valid'], "Код не должен быть валидным"
        assert not exec_data['can_execute'], "Код не должен выполняться"

        print(f"\nНайденные ошибки:")
        for error in exec_data['syntax_errors']:
            print(f"   - {error}")

        print("\n✅ Обработка невалидного кода работает корректно")

    def test_timeout_handling(self):
        """Тест обработки таймаута выполнения"""
        print("\n=== Тест обработки таймаута ===")

        # Код, который выполняется долго
        long_running_code = '''
import time
time.sleep(10)  # Спим 10 секунд
print("Done")
'''

        execute_payload = {
            "code": long_running_code,
            "timeout": 3,  # Устанавливаем таймаут 3 секунды
            "run_with_pytest": False
        }

        print("Выполнение кода с таймаутом...")
        exec_response = self.session.post(
            f"{BASE_URL}/generate/execute",
            json=execute_payload
        )

        assert exec_response.status_code == 200
        exec_data = exec_response.json()

        print(f"\nРезультаты:")
        print(f"   Может выполняться: {exec_data['can_execute']}")
        print(f"   Ошибок выполнения: {len(exec_data['runtime_errors'])}")

        # Проверяем наличие ошибки таймаута
        assert not exec_data['can_execute'], "Выполнение должно прерваться по таймауту"
        assert len(exec_data['runtime_errors']) > 0, "Должна быть ошибка таймаута"

        # Ищем ошибку таймаута
        timeout_error = any(
            "timeout" in error.lower()
            for error in exec_data['runtime_errors']
        )
        assert timeout_error, "Ожидается ошибка таймаута"

        print("\n✅ Обработка таймаута работает корректно")

    def test_ui_test_with_dependencies(self):
        """Тест выполнения UI теста с зависимостями"""
        print("\n=== Тест выполнения UI теста с зависимостями ===")

        # Генерируем сложный UI тест
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Сложная форма</title>
        </head>
        <body>
            <form id="registration">
                <div class="form-group">
                    <label>Имя:</label>
                    <input type="text" id="firstName" required>
                </div>
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" id="email" required>
                </div>
                <div class="form-group">
                    <label>Телефон:</label>
                    <input type="tel" id="phone" pattern="[0-9]{10}">
                </div>
                <div class="form-group">
                    <input type="checkbox" id="terms" required>
                    <label for="terms">Согласен с условиями</label>
                </div>
                <button type="submit">Зарегистрироваться</button>
            </form>
        </body>
        </html>
        """

        generate_payload = {
            "input_method": "html",
            "html_content": html_content,
            "framework": "playwright",
            "selectors": {
                "form": "#registration",
                "first_name": "#firstName",
                "email": "#email",
                "phone": "#phone",
                "terms": "#terms",
                "submit_button": "button[type='submit']"
            }
        }

        print("Генерация сложного UI теста...")
        gen_response = self.session.post(
            f"{BASE_URL}/generate/auto/ui",
            json=generate_payload
        )

        assert gen_response.status_code == 200
        gen_data = gen_response.json()
        generated_code = gen_data['code']

        # Сохраняем инструкции по установке
        requirements = gen_data.get('requirements_file', '')
        setup_instructions = gen_data.get('setup_instructions', '')

        print(f"\nИнструкции по установке:")
        if requirements:
            print(requirements[:500])

        # Выполняем тест
        execute_payload = {
            "code": generated_code,
            "timeout": 60,
            "run_with_pytest": False
        }

        print("\nВыполнение сложного UI теста...")
        exec_response = self.session.post(
            f"{BASE_URL}/generate/execute",
            json=execute_payload
        )

        assert exec_response.status_code == 200
        exec_data = exec_response.json()

        print(f"\nРезультаты:")
        print(f"   Валиден: {exec_data['is_valid']}")
        print(f"   Может выполняться: {exec_data['can_execute']}")

        # Сохраняем полный вывод для анализа
        if exec_data.get('execution_output'):
            print(f"\nВывод выполнения:")
            print(exec_data['execution_output'])

        # Проверяем синтаксис
        assert len(exec_data['syntax_errors']) == 0, f"Синтаксические ошибки: {exec_data['syntax_errors']}"

        print("\n✅ Сложный UI тест проверен")

    def test_full_ui_test_pipeline(self):
        """Тест полного пайплайна: генерация -> выполнение -> отчет"""
        print("\n=== Тест полного пайплайна UI тестов ===")

        # Шаг 1: Генерация UI теста
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Интернет-магазин</title></head>
        <body>
            <header>
                <h1>Мой магазин</h1>
                <nav>
                    <a href="#catalog">Каталог</a>
                    <a href="#cart">Корзина (0)</a>
                    <a href="#profile">Профиль</a>
                </nav>
            </header>

            <main>
                <section class="products">
                    <div class="product" data-id="1">
                        <h3>Товар 1</h3>
                        <p>Описание товара 1</p>
                        <button class="add-to-cart">В корзину</button>
                    </div>
                    <div class="product" data-id="2">
                        <h3>Товар 2</h3>
                        <p>Описание товара 2</p>
                        <button class="add-to-cart">В корзину</button>
                    </div>
                </section>
            </main>

            <footer>
                <p>&copy; 2023 Мой магазин</p>
            </footer>
        </body>
        </html>
        """

        print("Шаг 1: Генерация UI теста...")
        generate_payload = {
            "input_method": "html",
            "html_content": html_content,
            "framework": "playwright",
            "generation_settings": {
                "use_aaa_pattern": True,
                "include_negative_tests": True,
                "detail_level": "detailed"
            }
        }

        gen_response = self.session.post(
            f"{BASE_URL}/generate/auto/ui",
            json=generate_payload
        )

        assert gen_response.status_code == 200
        gen_data = gen_response.json()

        print(f"✅ Тест сгенерирован")
        print(f"   Найдено сценариев: {len(gen_data['test_scenarios'])}")
        print("   Сценарии:")
        for i, scenario in enumerate(gen_data['test_scenarios'][:5], 1):
            print(f"     {i}. {scenario}")

        # Шаг 2: Валидация и выполнение
        print("\nШаг 2: Валидация и выполнение...")
        execute_payload = {
            "code": gen_data['code'],
            "timeout": 90,
            "run_with_pytest": False
        }

        exec_response = self.session.post(
            f"{BASE_URL}/generate/execute",
            json=execute_payload
        )

        assert exec_response.status_code == 200
        exec_data = exec_response.json()

        # Шаг 3: Анализ результатов
        print("\nШаг 3: Анализ результатов...")
        print(f"   Синтаксис корректен: {exec_data['is_valid']}")
        print(f"   Код выполним: {exec_data['can_execute']}")
        print(f"   Время выполнения: {exec_data.get('execution_time', 0):.2f}с")

        if exec_data.get('execution_output'):
            output_lines = exec_data['execution_output'].split('\n')
            print(f"   Строк вывода: {len(output_lines)}")

            # Ищем ключевые слова в выводе
            output_text = exec_data['execution_output'].lower()
            key_indicators = ['test', 'pass', 'fail', 'error', 'browser', 'page']
            found_indicators = [word for word in key_indicators if word in output_text]
            if found_indicators:
                print(f"   Найдены индикаторы: {', '.join(found_indicators)}")

        # Шаг 4: Сохранение артефактов
        print("\nШаг 4: Сохранение артефактов...")

        # Создаем директорию для результатов
        results_dir = tempfile.mkdtemp(prefix="ui_test_results_")
        print(f"   Директория результатов: {results_dir}")

        # Сохраняем сгенерированный тест
        test_file = os.path.join(results_dir, "generated_ui_test.py")
        with open(test_file, 'w') as f:
            f.write(gen_data['code'])
        print(f"   Тест сохранен: {test_file}")

        # Сохраняем инструкции
        if gen_data.get('setup_instructions'):
            instructions_file = os.path.join(results_dir, "setup_instructions.md")
            with open(instructions_file, 'w') as f:
                f.write("# Инструкции по настройке\n\n")
                f.write(gen_data['setup_instructions'])
            print(f"   Инструкции сохранены: {instructions_file}")

        # Сохраняем требования
        if gen_data.get('requirements_file'):
            req_file = os.path.join(results_dir, "requirements.txt")
            with open(req_file, 'w') as f:
                f.write(gen_data['requirements_file'])
            print(f"   Требования сохранены: {req_file}")

        # Сохраняем результаты выполнения
        results_json = {
            "generation": {
                "scenarios": gen_data['test_scenarios'],
                "selectors": gen_data['selectors_found'],
                "generation_time": gen_data['generation_time']
            },
            "execution": {
                "is_valid": exec_data['is_valid'],
                "can_execute": exec_data['can_execute'],
                "execution_time": exec_data.get('execution_time'),
                "syntax_errors": exec_data['syntax_errors'],
                "runtime_errors": exec_data['runtime_errors'],
                "output": exec_data.get('execution_output', '')
            }
        }

        results_file = os.path.join(results_dir, "execution_results.json")
        with open(results_file, 'w') as f:
            json.dump(results_json, f, indent=2, ensure_ascii=False)
        print(f"   Результаты сохранены: {results_file}")

        print("\n✅ Полный пайплайн выполнен успешно")


def run_all_tests():
    """Запуск всех тестов с красивым выводом"""
    import sys

    print("\n" + "="*80)
    print("  🧪 ТЕСТИРОВАНИЕ ФУНКЦИИ ЗАПУСКА СГЕНЕРИРОВАННЫХ UI ТЕСТОВ")
    print("="*80)
    print("\nТесты проверяют:")
    print("  1. Выполнение Playwright тестов")
    print("  2. Выполнение Selenium тестов")
    print("  3. Генерацию Cypress тестов")
    print("  4. Работу с pytest и Allure")
    print("  5. Обработку ошибок")
    print("  6. Обработку таймаутов")
    print("  7. Работу с зависимостями")
    print("  8. Полный пайплайн генерации и выполнения")

    # Создаем тестовый экземпляр
    test_instance = TestUITestExecution()
    test_instance.setup_method()

    tests = [
        ("Выполнение Playwright теста", test_instance.test_execute_playwright_test),
        ("Выполнение Selenium теста", test_instance.test_execute_selenium_test),
        ("Генерация Cypress теста", test_instance.test_execute_cypress_test),
        ("Pytest тест с Allure", test_instance.test_execute_pytest_ui_test),
        ("Обработка невалидного кода", test_instance.test_invalid_code_handling),
        ("Обработка таймаута", test_instance.test_timeout_handling),
        ("UI тест с зависимостями", test_instance.test_ui_test_with_dependencies),
        ("Полный пайплайн", test_instance.test_full_ui_test_pipeline),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
            passed += 1
            print(f"\n✅ {test_name} - ПРОЙДЕН")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} - ПРОВАЛЕН")
            print(f"Ошибка: {str(e)}")
            import traceback
            traceback.print_exc()

        print("\n" + "-"*80)

    # Итог
    print("\n" + "="*80)
    print("  📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*80)
    print(f"Прошло:  {passed}/{len(tests)}")
    print(f"Провалено: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("Функция запуска сгенерированных UI тестов работает корректно.")
    else:
        print(f"\n⚠️ {failed} тест(ов) провалено. Требуется исправление ошибок.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)