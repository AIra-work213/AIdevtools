# Техническое задание: ML/AI модуль TestOps Copilot

## 1. Общие положения

### 1.1. Назначение
Разработка интеллектуального ядра системы на базе Cloud.ru Evolution Foundation Model для автоматизации генерации, анализа и оптимизации тестового кода.

### 1.2. Задачи модуля
- Генерация тестового кода из натурального языка
- Анализ и валидация существующих тестов
- Поиск семантических дубликатов
- Оптимизация и рефакторинг тестов
- Извлечение знаний из документации

## 2. Архитектура ML/AI системы

### 2.1. Компоненты
```
ai_core/
├── llm/                # Работа с LLM
│   ├── client.py       # Клиент Cloud.ru Evolution
│   ├── prompts.py      # Управление промптами
│   └── models.py       # Модели ответов
├── embedding/          # Векторные представления
│   ├── encoder.py      # Энкодер текста
│   ├── similarity.py   # Расчет схожести
│   └── clustering.py   # Кластеризация тестов
├── rag/                # RAG система
│   ├── retriever.py    # Поиск релевантного контекста
│   ├── knowledge_base.py # База знаний
│   └── indexer.py      # Индексация документов
├── parsing/            # Парсинг спецификаций
│   ├── openapi.py      # Парсер OpenAPI
│   ├── html.py         # Парсер HTML/UI
│   └── code.py         # AST парсер Python
├── generation/         # Генерация кода
│   ├── manual_tests.py # Генератор ручных тестов
│   ├── api_tests.py    # Генератор API тестов
│   └── ui_tests.py     # Генератор UI тестов
├── analysis/           # Анализ кода
│   ├── validator.py    # Валидатор стандартов
│   ├── linter.py       # Линтер
│   └── optimizer.py    # Оптимизатор
└── utils/              # Утилиты
    ├── templates.py    # Шаблоны кода
    └── helpers.py      # Вспомогательные функции
```

### 2.2. Потоки данных

#### 2.2.1. Генерация тестов
```
Пользовательский ввод → Парсинг → RAG (контекст) → LLM (генерация) → Валидация → Вывод
```

#### 2.2.2. Анализ тестов
```
Код → AST парсинг → Извлечение фич → Векторизация → Сравнение → Отчет
```

## 3. Интеграция с Cloud.ru Evolution

### 3.1. Клиент API
```python
from openai import OpenAI
import os
from typing import List, Dict, AsyncGenerator

class CloudEvolutionClient:
    """Клиент для работы с Cloud.ru Evolution API"""

    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ["CLOUD_API_KEY"],
            base_url="https://foundation-models.api.cloud.ru/v1"
        )
        self.model = "Qwen/Qwen3-Coder-480B-A35B-Instruct"

    async def chat_completion(
        self,
        messages: List[Dict],
        max_tokens: int = 4000,
        temperature: float = 0.3,
        stream: bool = False
    ) -> str | AsyncGenerator:
        """Отправка запроса к LLM"""

        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "presence_penalty": 0,
            "top_p": 0.95
        }

        if stream:
            return self._stream_response(params)
        else:
            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message.content

    async def get_embedding(self, text: str) -> List[float]:
        """Получение эмбеддинга текста"""
        # Используем внутреннюю модель или внешнюю
        pass
```

### 3.2. Управление промптами
```python
class PromptManager:
    """Управление системными промптами"""

    SYSTEM_PROMPTS = {
        "manual_tester": """
        Ты - senior QA инженер с 10-летним опытом в автоматизации тестирования.
        Твоя задача - генерировать качественные тесты на Python с использованием Allure.

        Принципы:
        1. Каждый тест должен следовать паттерну AAA (Arrange-Act-Assert)
        2. Используй декораторы @allure.* для документации
        3. Каждый шаг оборачивай in with allure.step(...)
        4. Добавляй осмысленные assert в конце
        5. Используй описательные названия тестов и шагов

        Формат вывода - только валидный Python код.
        """,

        "api_tester": """
        Ты - expert в API тестировании.
        Генерируй pytest тесты для OpenAPI спецификаций.

        Правила:
        1. Тестируй позитивные сценарии (200 OK)
        2. Тестируй негативные сценарии (400, 401, 403, 404, 500)
        3. Валидируй JSON schema ответов
        4. Используй fixtures для подготовки данных
        5. Добавляй параметризованные тесты для граничных значений
        """,

        "code_analyzer": """
        Ты - code reviewer специализирующийся на test automation.
        Анализируй Python код тестов на соответствие стандартам:

        Стандарты:
        1. Наличие @allure.feature, @allure.story, @allure.title
        2. Использование паттерна AAA
        3. Обработка исключений
        4. Читаемость и поддерживаемость
        5. Отсутствие дублирования кода
        """
    }

    def build_prompt(self, task_type: str, context: Dict) -> List[Dict]:
        """Сборка промпта из системной части и контекста"""
        system_prompt = self.SYSTEM_PROMPTS[task_type]
        user_prompt = self._format_context(context)

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def _format_context(self, context: Dict) -> str:
        """Форматирование контекста в промпт"""
        pass
```

## 4. RAG (Retrieval Augmented Generation)

### 4.1. База знаний
```python
class KnowledgeBase:
    """База знаний для RAG системы"""

    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.documents = {}

    async def add_document(self, doc_id: str, content: str, metadata: Dict):
        """Добавление документа в базу знаний"""
        # Чанкинг документа
        chunks = self._chunk_document(content)

        # Генерация эмбеддингов
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"
            embedding = await self._get_embedding(chunk)

            self.vector_store.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{**metadata, "chunk_id": i}]
            )

    async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Поиск релевантных документов"""
        query_embedding = await self._get_embedding(query)

        results = self.vector_store.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        return self._format_results(results)

    def _chunk_document(self, content: str, chunk_size: int = 1000) -> List[str]:
        """Разделение документа на чанки"""
        pass
```

### 4.2. Индексация документации
```python
class DocumentationIndexer:
    """Индексация документации по тестированию"""

    DOCUMENTATION_SOURCES = [
        "https://docs.qameta.io/allure/",
        "https://docs.pytest.org/",
        "https://playwright.dev/python/",
        "company_testing_guidelines.pdf"
    ]

    async def index_all(self):
        """Индексация всех источников документации"""
        for source in self.DOCUMENTATION_SOURCES:
            if source.endswith(".pdf"):
                await self._index_pdf(source)
            elif source.startswith("http"):
                await self._index_website(source)
            else:
                await self._index_file(source)
```

## 5. Векторные представления и поиск

### 5.1. Энкодер
```python
from sentence_transformers import SentenceTransformer
import numpy as np

class TextEncoder:
    """Энкодер текста в векторные представления"""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        self.model = SentenceTransformer(model_name)

    async def encode(self, texts: List[str]) -> np.ndarray:
        """Кодирование текстов в эмбеддинги"""
        # Batch encoding для оптимизации
        return self.model.encode(texts, normalize_embeddings=True)

    def encode_single(self, text: str) -> np.ndarray:
        """Кодирование одного текста"""
        return self.model.encode([text], normalize_embeddings=True)[0]
```

### 5.2. Поиск дубликатов
```python
class DuplicateDetector:
    """Детектор семантических дубликатов тестов"""

    def __init__(self, encoder: TextEncoder, threshold: float = 0.85):
        self.encoder = encoder
        self.threshold = threshold

    async def find_duplicates(self, test_cases: List[TestCase]) -> List[DuplicateGroup]:
        """Поиск групп дубликатов"""
        # Извлечение текста из тестов
        texts = [self._extract_test_text(tc) for tc in test_cases]

        # Генерация эмбеддингов
        embeddings = await self.encoder.encode(texts)

        # Расчет матрицы схожести
        similarity_matrix = self._compute_similarity(embeddings)

        # Кластеризация дубликатов
        duplicate_groups = self._cluster_duplicates(
            similarity_matrix,
            test_cases
        )

        return duplicate_groups

    def _extract_test_text(self, test_case: TestCase) -> str:
        """Извлечение текстового представления теста"""
        return f"{test_case.title} {test_case.code}"

    def _compute_similarity(self, embeddings: np.ndarray) -> np.ndarray:
        """Расчет матрицы косинусной схожести"""
        return embeddings @ embeddings.T
```

## 6. Генераторы кода

### 6.1. Генератор ручных тестов
```python
class ManualTestGenerator:
    """Генератор кода ручных тестов"""

    def __init__(self, llm_client: CloudEvolutionClient, prompt_manager: PromptManager):
        self.llm = llm_client
        self.prompt_manager = prompt_manager

    async def generate(
        self,
        requirements: str,
        metadata: Optional[Dict] = None
    ) -> GeneratedTest:
        """Генерация ручных тестов из требований"""

        # Извлечение критериев приемки
        acceptance_criteria = await self._extract_acceptance_criteria(requirements)

        # Декомпозиция на сценарии
        scenarios = await self._decompose_to_scenarios(acceptance_criteria)

        # Генерация кода для каждого сценария
        test_code = await self._generate_test_code(scenarios, metadata)

        # Валидация сгенерированного кода
        validation = await self._validate_code(test_code)

        return GeneratedTest(
            code=test_code,
            scenarios=scenarios,
            validation=validation
        )

    async def _extract_acceptance_criteria(self, requirements: str) -> List[str]:
        """Извлечение критериев приемки из текста"""
        prompt = self.prompt_manager.build_prompt(
            "criteria_extractor",
            {"requirements": requirements}
        )

        response = await self.llm.chat_completion(prompt)
        return self._parse_criteria(response)

    async def _decompose_to_scenarios(self, criteria: List[str]) -> List[TestScenario]:
        """Декомпозиция критериев в тестовые сценарии"""
        pass
```

### 6.2. Генератор API тестов
```python
class ApiTestGenerator:
    """Генератор кода API тестов из OpenAPI спецификации"""

    def __init__(self, llm_client, openapi_parser):
        self.llm = llm_client
        self.parser = openapi_parser

    async def generate(
        self,
        openapi_spec: str,
        endpoints_filter: Optional[List[str]] = None,
        test_types: List[str] = ["happy_path", "negative"]
    ) -> GeneratedTest:
        """Генерация API тестов из спецификации"""

        # Парсинг OpenAPI
        api_info = self.parser.parse(openapi_spec)

        # Фильтрация эндпоинтов
        if endpoints_filter:
            api_info.endpoints = [
                ep for ep in api_info.endpoints
                if ep.path in endpoints_filter
            ]

        # Генерация тестов для каждого эндпоинта
        test_cases = []
        for endpoint in api_info.endpoints:
            for test_type in test_types:
                test_case = await self._generate_endpoint_test(
                    endpoint, test_type, api_info
                )
                test_cases.append(test_case)

        # Компиляция всех тестов в файл
        test_code = self._compile_test_file(test_cases, api_info)

        return GeneratedTest(
            code=test_code,
            test_cases=test_cases,
            coverage=self._calculate_coverage(api_info, test_cases)
        )
```

## 7. Анализаторы кода

### 7.1. Валидатор стандартов
```python
class CodeValidator:
    """Валидатор кода тестов на соответствие стандартам"""

    def __init__(self):
        self.rules = self._load_validation_rules()

    async def validate(self, code: str) -> ValidationResult:
        """Валидация Python кода"""
        issues = []

        # Синтаксическая валидация
        syntax_result = self._validate_syntax(code)
        if not syntax_result.is_valid:
            return syntax_result

        # Парсинг AST
        tree = ast.parse(code)

        # Проверка декораторов
        decorator_issues = self._check_decorators(tree)
        issues.extend(decorator_issues)

        # Проверка структуры AAA
        structure_issues = self._check_aaa_structure(tree)
        issues.extend(structure_issues)

        # Проверка именования
        naming_issues = self._check_naming_conventions(tree)
        issues.extend(naming_issues)

        return ValidationResult(
            is_valid=len(issues) == 0,
            errors=[i for i in issues if i.severity == "error"],
            warnings=[i for i in issues if i.severity == "warning"]
        )

    def _check_decorators(self, tree: ast.AST) -> List[ValidationIssue]:
        """Проверка наличия обязательных декораторов"""
        issues = []
        required_decorators = ["allure.feature", "allure.story", "allure.title"]

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                present_decorators = []

                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Attribute):
                        decorator_name = f"{decorator.value.id}.{decorator.attr}"
                        present_decorators.append(decorator_name)

                for required in required_decorators:
                    if required not in present_decorators:
                        issues.append(ValidationIssue(
                            line=node.lineno,
                            message=f"Отсутствует декоратор @{required}",
                            severity="error"
                        ))

        return issues
```

### 7.2. Оптимизатор кода
```python
class CodeOptimizer:
    """Оптимизатор и рефакторинг тестового кода"""

    async def optimize(self, code: str) -> OptimizationResult:
        """Оптимизация тестового кода"""

        # Анализ проблем
        issues = await self._analyze_issues(code)

        # Генерация исправлений
        fixes = []
        for issue in issues:
            fix = await self._generate_fix(issue, code)
            fixes.append(fix)

        # Применение исправлений
        optimized_code = self._apply_fixes(code, fixes)

        return OptimizationResult(
            original_code=code,
            optimized_code=optimized_code,
            fixes=fixes,
            improvement_score=self._calculate_improvement(issues)
        )

    async def _analyze_issues(self, code: str) -> List[CodeIssue]:
        """Анализ проблем в коде"""
        issues = []

        # Поиск дублирования
        duplicates = await self._find_duplicates(code)
        issues.extend(duplicates)

        # Поиск сложных методов
        complex_methods = self._find_complex_methods(code)
        issues.extend(complex_methods)

        # Поиск "магических чисел"
        magic_numbers = self._find_magic_numbers(code)
        issues.extend(magic_numbers)

        return issues
```

## 8. Обработка неструктурированных данных

### 8.1. Извлечение требований
```python
class RequirementsExtractor:
    """Извлечение структурированных требований из текста"""

    async def extract(
        self,
        text: str,
        format_type: str = "user_story"
    ) -> StructuredRequirements:
        """Извлечение требований из текста"""

        if format_type == "user_story":
            return await self._extract_from_user_story(text)
        elif format_type == "acceptance_criteria":
            return await self._extract_from_ac(text)
        else:
            return await self._extract_general(text)

    async def _extract_from_user_story(self, text: str) -> StructuredRequirements:
        """Извлечение из User Story формата"""
        # Поиск паттернов "As a user, I want to..."
        # Извлечение критериев приемки
        pass
```

### 8.2. Анализ изображений (для будущих версий)
```python
class ImageAnalyzer:
    """Анализ скриншотов UI для генерации тестов"""

    async def analyze_screenshot(self, image_bytes: bytes) -> UIAnalysis:
        """Анализ скриншота интерфейса"""

        # OCR для извлечения текста
        text_elements = await self._extract_text(image_bytes)

        # Детекция элементов UI
        ui_elements = await self._detect_ui_elements(image_bytes)

        # Построение иерархии элементов
        element_hierarchy = self._build_hierarchy(ui_elements)

        return UIAnalysis(
            text=text_elements,
            elements=ui_elements,
            hierarchy=element_hierarchy
        )
```

## 9. Кэширование и оптимизация

### 9.1. Кэширование LLM ответов
```python
import hashlib
from functools import lru_cache
import redis

class LLMCache:
    """Кэширование ответов LLM для идентичных запросов"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.local_cache = {}

    def get_cache_key(self, prompt: str, **kwargs) -> str:
        """Генерация ключа кэша"""
        key_data = f"{prompt}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get(self, prompt: str, **kwargs) -> Optional[str]:
        """Получение кэшированного ответа"""
        key = self.get_cache_key(prompt, **kwargs)

        # Сначала проверяем локальный кэш
        if key in self.local_cache:
            return self.local_cache[key]

        # Затем Redis
        cached = await self.redis.get(key)
        if cached:
            self.local_cache[key] = cached
            return cached

        return None

    async def set(self, prompt: str, response: str, ttl: int = 3600, **kwargs):
        """Сохранение ответа в кэш"""
        key = self.get_cache_key(prompt, **kwargs)

        # Сохраняем в Redis
        await self.redis.setex(key, ttl, response)

        # И в локальный кэш
        self.local_cache[key] = response
```

### 9.2. Batch обработка
```python
class BatchProcessor:
    """Пакетная обработка запросов к LLM"""

    def __init__(self, llm_client, batch_size: int = 5):
        self.llm = llm_client
        self.batch_size = batch_size
        self.queue = asyncio.Queue()

    async def add_request(self, prompt: str) -> str:
        """Добавление запроса в очередь"""
        future = asyncio.Future()
        await self.queue.put((prompt, future))
        return await future

    async def process_queue(self):
        """Обработка очереди пакетами"""
        while True:
            batch = []

            # Собираем батч
            for _ in range(self.batch_size):
                if self.queue.empty():
                    break
                item = await self.queue.get()
                batch.append(item)

            if not batch:
                await asyncio.sleep(0.1)
                continue

            # Параллельная обработка
            tasks = [
                self.llm.chat_completion([{"role": "user", "content": prompt}])
                for prompt, _ in batch
            ]

            results = await asyncio.gather(*tasks)

            # Распределение результатов
            for (_, future), result in zip(batch, results):
                future.set_result(result)
```

## 10. Мониторинг и метрики

### 10.1. Метрики качества генерации
```python
class QualityMetrics:
    """Сбор метрик качества генерации"""

    def __init__(self):
        self.metrics = {
            "syntax_validity": [],
            "test_coverage": [],
            "user_satisfaction": [],
            "generation_time": []
        }

    def record_generation(
        self,
        is_valid: bool,
        coverage: float,
        time_taken: float,
        user_rating: Optional[int] = None
    ):
        """Запись метрик генерации"""
        self.metrics["syntax_validity"].append(is_valid)
        self.metrics["test_coverage"].append(coverage)
        self.metrics["generation_time"].append(time_taken)

        if user_rating:
            self.metrics["user_satisfaction"].append(user_rating)

    def get_quality_score(self) -> float:
        """Расчет общего показателя качества"""
        validity_rate = np.mean(self.metrics["syntax_validity"])
        avg_coverage = np.mean(self.metrics["test_coverage"])
        avg_satisfaction = np.mean(
            self.metrics["user_satisfaction"] or [0]
        )

        return (validity_rate * 0.4 +
                avg_coverage * 0.4 +
                avg_satisfaction * 0.2)
```

## 11. Тестирование ML/AI модуля

### 11.1. Unit тесты
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_manual_test_generator():
    """Тест генератора ручных тестов"""
    generator = ManualTestGenerator(mock_llm, mock_prompt_manager)

    with patch.object(generator, '_extract_acceptance_criteria') as mock_extract:
        mock_extract.return_value = ["User should be able to login"]

        result = await generator.generate(
            "Implement login functionality test"
        )

        assert "@allure.feature" in result.code
        assert "def test_" in result.code
        assert result.validation.is_valid
```

### 11.2. Интеграционные тесты
```python
@pytest.mark.integration
async def test_full_generation_pipeline():
    """Тест полного пайплайна генерации"""
    requirements = """
    User should be able to:
    1. Login with valid credentials
    2. See error with invalid password
    3. Reset password
    """

    # Генерация
    generator = ManualTestGenerator(llm_client, prompt_manager)
    result = await generator.generate(requirements)

    # Валидация
    validator = CodeValidator()
    validation = await validator.validate(result.code)

    # Проверки
    assert validation.is_valid
    assert len(result.scenarios) >= 3
    assert "test_login" in result.code.lower()
```

## 12. Производительность и масштабирование

### 12.1. Оптимизации
- Использование batch processing для LLM запросов
- Интеллектуальное кэширование
- Параллельная обработка независимых задач
- Предварительная индексация документации

### 12.2. Требования
- Время генерации теста < 45 секунд
- Время ответа на валидацию < 5 секунд
- Поиск дубликатов в 1000 тестов < 10 секунд
- Поддержка 10 одновременных пользователей

## 13. Безопасность

### 13.1. Безопасность промптов
- Санитизация пользовательского ввода
- Предотвращение prompt injection
- Ограничение длины промптов

### 13.2. Конфиденциальность
- Не хранить чувствительные данные в промптах
- Анонимизация кода перед отправкой
- Логирование без содержимого запросов