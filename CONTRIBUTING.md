# 🤝 Contributing to AI TestOps Copilot

Спасибо за интерес к развитию проекта! Мы ценим любой вклад — от исправления опечаток до предложения новых фич.

## 🚀 Как начать

### 1. Fork и Clone

```bash
# Fork репозиторий на GitHub, затем:
git clone https://github.com/your-username/AIdevtools.git
cd AIdevtools
git remote add upstream https://github.com/original-repo/AIdevtools.git
```

### 2. Настройка окружения

```bash
# Создайте ветку для вашей фичи
git checkout -b feature/your-feature-name

# Настройте .env файл
cp .env.example .env
# Добавьте необходимые переменные окружения

# Запустите проект
docker-compose up --build
```

## 📝 Руководство по вкладу

### 🔧 Багфиксы

1. Создайте issue с описанием бага
2. Добавьте теги: `[BUG]`
3. В вашем PR ссылайтесь на issue

### ✨ Новые фичи

1. Обсудите идею в issue перед реализацией
2. Создайте ветку: `feature/feature-name`
3. Следуйте архитектурным принципам проекта
4. Добавьте тесты

### 📚 Документация

- Улучшение README
- Добавление примеров
- Обновление документации API

### 🧪 Тесты

- Unit тесты для новой логики
- Integration тесты для API
- E2E тесты для UI фич

## 🏗️ Архитектурные принципы

### Код генерации тестов

```python
# Пример хорошего промпта для LLM
prompt_template = """
Generate robust Selenium test for URL: {url}

Requirements:
1. Use explicit waits (WebDriverWait)
2. Prefer CSS selectors over XPath
3. Include meaningful assertions
4. Add Allure decorators
5. Handle potential errors gracefully

Page context: {page_analysis}
"""

# Генерация с использованием ансамбля
async def generate_with_ensemble(url: str):
    tasks = [
        model1.generate(prompt),
        model2.generate(prompt),
        model3.generate(prompt)
    ]
    results = await asyncio.gather(*tasks)
    return aggregate_code(results)
```

### Структура проекта

```
src/
├── ai-core/
│   ├── generation/      # Логика генерации тестов
│   ├── aggregation/     # Агрегация кода от разных моделей
│   └── validation/      # Валидация сгенерированного кода
├── backend/
│   ├── api/            # FastAPI эндпоинты
│   ├── services/       # Бизнес-логика
│   └── models/         # Pydantic модели
└── frontend/
    ├── components/     # React компоненты
    ├── hooks/          # Custom hooks
    └── utils/          # Утилиты
```

## 🎯 Области для улучшения

### 1. Промпт инжиниринг

```python
# Улучшение промптов для лучших результатов
IMPROVED_PROMPT = """
You are an expert QA Engineer generating automated tests.

Context:
- URL: {url}
- Page Analysis: {dom_structure}
- Interactive Elements: {elements}

Generate test that:
1. Tests critical user journeys
2. Uses reliable selectors (ID > data-testid > class)
3. Includes proper error handling
4. Is compatible with Docker execution
5. Provides clear step descriptions

Best Practices:
- Use Page Object Pattern for complex pages
- Add comprehensive assertions
- Include negative test cases
- Test responsiveness if applicable
"""
```

### 2. Стратегии агрегации

```python
# Улучшение алгоритма слияния кода
def aggregate_improved(codes: List[str]) -> str:
    """
    Умная агрегация с анализом:
    - Надежности селекторов
    - Покрытия тестовых сценариев
    - Качества проверок
    - Читаемости кода
    """
    scores = []
    for code in codes:
        score = evaluate_code_quality(code)
        scores.append((code, score))

    # Выбираем лучшее и улучшаем элементами из других
    best_code = max(scores, key=lambda x: x[1])[0]
    return enhance_with_best_practices(best_code, codes)
```

### 3. Self-Healing механизмы

```python
# Автоисправление падающих тестов
async def self_heal_test(test_code: str, error_log: str) -> str:
    """
    Анализирует ошибку и генерирует исправленный код
    """
    healing_prompt = f"""
    Test failed with error:
    {error_log}

    Test code:
    {test_code}

    Fix the test to handle this error gracefully.
    Maintain the original test intent.
    """

    return await llm.generate(healing_prompt)
```

## 🧪 Тестирование изменений

### Запуск тестов

```bash
# Unit тесты
pytest src/backend/tests/

# Интеграционные тесты
pytest test_suite/integration/

# E2E тесты
pytest test_suite/e2e/

# Генерация тестов
python test_suite/test_generation.py
```

### Код качества

```bash
# Linting
flake8 src/
black src/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

## 📝 Pull Request Process

1. **Update documentation** - Если изменения затрагивают API
2. **Add tests** - Покрытие новых фич
3. **Follow commit convention**:
   ```
   feat: add new test generation feature
   fix: resolve issue with selector reliability
   docs: update API documentation
   test: add integration tests for aggregation
   ```

4. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   ```

## 🎖️ Рекомендации для развития

### Junior Contributors

- Начните с документации и тестов
- Изучите архитектуру в [ARCHITECTURE.md](ARCHITECTURE.md)
- Попробуйте исправить простые баги

### Mid-level Contributors

- Улучшение промптов
- Оптимизация агрегации
- Добавление новых типов тестов

### Senior Contributors

- Новые стратегии self-healing
- Интеграция с новыми LLM
- Архитектурные улучшения

## 💬 Куда обращаться за помощью

- **Issues** - для багов и фич-реквестов
- **Discussions** - для вопросов и идей
- **Discord/Slack** - для общения в реальном времени

## 🏆 Recognition

Best contributors:
- 🌟 Feature recognition in release notes
- 🏷️ Contributor badge in documentation
- 🎁 Swag for significant contributions
- 💡 Speaking opportunities at events

---

Спасибо за ваш вклад в будущее автоматизации тестирования! 🚀