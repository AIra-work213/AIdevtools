# Техническое задание: Backend API TestOps Copilot

## 1. Общие положения

### 1.1. Назначение
Разработка REST API сервиса для оркестрации запросов к AI модулям и интеграции с внешними системами (GitLab, Allure TestOps).

### 1.2. Архитектурные принципы
- Асинхронная архитектура на FastAPI
- Миксервисный подход с четким разделением ответственности
- Event-driven коммуникация между модулями
- Full type hints с pydantic моделями

## 2. Стек технологий

- **Framework**: FastAPI 0.104+
- **Python**: 3.10+
- **Асинхронность**: asyncio, aioredis
- **База данных**: PostgreSQL (relational) + ChromaDB (vector)
- **ORM**: SQLAlchemy 2.0 + asyncpg
- **Миграции**: Alembic
- **Аутентификация**: JWT + OAuth2
- **Валидация**: Pydantic V2
- **Логирование**: structlog
- **Мониторинг**: Prometheus + Sentry

## 3. Архитектура

### 3.1. Структура проекта
```
src/
├── app/
│   ├── api/              # API роуты
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── generate.py
│   │   │   │   ├── analyze.py
│   │   │   │   └── gitlab.py
│   │   │   └── router.py
│   ├── core/             # Конфигурация
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── models/           # SQLAlchemy модели
│   ├── schemas/          # Pydantic схемы
│   ├── services/         # Бизнес-логика
│   │   ├── ai_service.py
│   │   ├── gitlab_service.py
│   │   ├── validation_service.py
│   │   └── vector_service.py
│   ├── repositories/     # Репозитории данных
│   ├── utils/            # Утилиты
│   └── main.py           # Application factory
```

### 3.2. Основные модули

#### 3.2.1. API Layer
- RESTful эндпоинты
- Валидация запросов/ответов
- Rate limiting
- CORS и middleware

#### 3.2.2. Service Layer
- Бизнес-логика
- Интеграция с внешними API
- Оркестрация AI запросов
- Обработка ошибок

#### 3.2.3. Data Layer
- Репозитории с CRUD операциями
- Транзакции
- Кэширование
- Миграции

## 4. API Эндпоинты

### 4.1. Генерация тестов
```python
# POST /api/v1/generate/manual
class ManualTestRequest(BaseModel):
    requirements: str = Field(..., min_length=10, max_length=10000)
    metadata: Optional[TestMetadata] = None

class TestMetadata(BaseModel):
    feature: Optional[str] = None
    story: Optional[str] = None
    owner: Optional[str] = None
    severity: Optional[str] = "normal"

class ManualTestResponse(BaseModel):
    code: str
    test_cases: List[TestCase]
    validation: ValidationResult
```

```python
# POST /api/v1/generate/auto/api
class ApiTestRequest(BaseModel):
    openapi_spec: str = Field(..., min_length=50)
    endpoint_filter: Optional[List[str]] = None
    test_types: List[str] = ["happy_path", "negative"]

class ApiTestResponse(BaseModel):
    code: str
    endpoints_covered: List[str]
    test_matrix: Dict[str, List[str]]
```

### 4.2. Анализ и валидация
```python
# POST /api/v1/analyze/validate
class ValidationRequest(BaseModel):
    code: str = Field(..., min_length=1)
    standards: Optional[List[str]] = ["allure"]

class ValidationResponse(BaseModel):
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    suggestions: List[str]
```

### 4.3. Поиск дубликатов
```python
# POST /api/v1/analyze/duplicates
class DuplicateSearchRequest(BaseModel):
    test_cases: List[TestCase]
    similarity_threshold: float = 0.85

class DuplicateSearchResponse(BaseModel):
    duplicates: List[DuplicateGroup]
    similarity_matrix: Dict[str, Dict[str, float]]
```

### 4.4. GitLab интеграция
```python
# POST /api/v1/gitlab/projects
async def get_projects() -> List[GitLabProject]

# POST /api/v1/gitlab/mr
class CreateMRRequest(BaseModel):
    project_id: int
    branch_name: str
    commit_message: str
    files: Dict[str, str]

class CreateMRResponse(BaseModel):
    mr_url: str
    mr_id: int
    status: str
```

## 5. Интеграция с AI сервисами

### 5.1. Cloud.ru Evolution API
```python
class AIClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.CLOUD_API_KEY,
            base_url="https://foundation-models.api.cloud.ru/v1"
        )

    async def generate_code(self, prompt: str) -> str:
        """Генерация кода тестов"""

    async def analyze_code(self, code: str) -> Dict:
        """Анализ кода на соответствие стандартам"""

    async def find_duplicates(self, tests: List[str]) -> List:
        """Поиск дубликатов с использованием эмбеддингов"""
```

### 5.2. Промпт инженеринг
```python
class PromptTemplates:
    MANUAL_TESTS = """
    Ты - QA инженер с 10 летним опытом. Сгенерируй Python код для Allure тестов на основе требований.

    Требования: {requirements}
    Метаданные: {metadata}

    Используй следующий формат:
    {code_template}

    Правила:
    1. Используй паттерн AAA (Arrange-Act-Assert)
    2. Добавляй декораторы @allure.* для каждого теста
    3. Каждое действие в with allure.step()
    4. Добавляй assert в конце каждого теста
    """

    API_TESTS = """
    Проанализируй OpenAPI спецификацию и сгенерируй pytest тесты.

    Спецификация:
    {openapi_spec}

    Эндпоинты для покрытия: {endpoints}

    Сгенерируй:
    1. Позитивные тесты (200 OK)
    2. Негативные тесты (400, 401, 404)
    3. Валидация JSON Schema
    """
```

## 6. Модели данных

### 6.1. SQLAlchemy модели
```python
# models/test_case.py
class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    feature = Column(String)
    story = Column(String)
    owner = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Векторное представление для поиска
    embedding = Column(ARRAY(Float), nullable=True)

    # Связи
    project_id = Column(Integer, ForeignKey("projects.id"))
```

### 6.2. Pydantic схемы
```python
# schemas/test_case.py
class TestCaseBase(BaseModel):
    title: str
    code: str
    feature: Optional[str] = None
    story: Optional[str] = None
    owner: Optional[str] = None

class TestCaseCreate(TestCaseBase):
    pass

class TestCase(TestCaseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## 7. Валидация и стандарты

### 7.1. Линтер Python кода
```python
class CodeValidator:
    REQUIRED_DECORATORS = ["@allure.feature", "@allure.story", "@allure.title"]

    async def validate_structure(self, code: str) -> ValidationResult:
        """Проверка структуры Allure теста"""
        errors = []

        # Проверка наличия декораторов
        if not all(dec in code for dec in self.REQUIRED_DECORATORS):
            errors.append("Отсутствуют обязательные декораторы")

        # Проверка паттерна AAA
        if "with allure.step" not in code:
            errors.append("Отсутствуют шаги AAA")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

### 7.2. Валидация синтаксиса
```python
async def validate_python_syntax(code: str) -> ValidationResult:
    """Проверка валидности Python кода"""
    try:
        compile(code, '<string>', 'exec')
        return ValidationResult(is_valid=True)
    except SyntaxError as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"SyntaxError: {e.msg} at line {e.lineno}"]
        )
```

## 8. Интеграция с внешними системами

### 8.1. GitLab API
```python
class GitLabService:
    def __init__(self):
        self.client = gitlab.Gitlab(
            settings.GITLAB_URL,
            private_token=settings.GITLAB_TOKEN
        )

    async def create_merge_request(
        self,
        project_id: int,
        branch_name: str,
        files: Dict[str, str]
    ) -> MergeRequestInfo:
        """Создание MR с тестами"""

    async def get_project_files(
        self,
        project_id: int,
        path: str = "tests"
    ) -> List[GitLabFile]:
        """Получение файлов тестов из репозитория"""
```

### 8.2. ChromaDB для векторного поиска
```python
class VectorStore:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name="test_cases"
        )

    async def add_test_case(self, test_case: TestCase):
        """Добавление теста в векторное хранилище"""
        embedding = await self.generate_embedding(test_case.title + test_case.code)
        self.collection.add(
            ids=[str(test_case.id)],
            embeddings=[embedding],
            documents=[test_case.code],
            metadatas=[{
                "title": test_case.title,
                "feature": test_case.feature
            }]
        )

    async def find_similar(
        self,
        query: str,
        threshold: float = 0.85
    ) -> List[SimilarTestCase]:
        """Поиск похожих тестов"""
```

## 9. Обработка ошибок

### 9.1. Кастомные исключения
```python
class TestOpsException(Exception):
    """Базовое исключение приложения"""

class AIServiceError(TestOpsException):
    """Ошибка AI сервиса"""

class GitLabError(TestOpsException):
    """Ошибка GitLab API"""

class ValidationError(TestOpsException):
    """Ошибка валидации кода"""
```

### 9.2. Error handling middleware
```python
@app.exception_handler(AIServiceError)
async def ai_service_error_handler(request: Request, exc: AIServiceError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "AI service unavailable",
            "detail": str(exc),
            "retry_after": 5
        }
    )
```

## 10. Производительность и масштабирование

### 10.1. Кэширование
```python
# Redis кэш для AI запросов
@lru_cache(maxsize=100)
async def get_cached_completion(prompt_hash: str):
    """Кэширование результатов AI генерации"""

# Кэш валидации
cache = TTLCache(maxsize=1000, ttl=300)
async def get_validation_result(code_hash: str):
    """Кэширование результатов валидации"""
```

### 10.2. Асинхронные операции
```python
# Параллельная обработка тестов
async def process_test_cases_batch(
    test_cases: List[TestCase]
) -> List[ProcessResult]:
    """Пакетная обработка тестов"""
    tasks = [
        process_single_test_case(test_case)
        for test_case in test_cases
    ]
    return await asyncio.gather(*tasks)
```

## 11. Безопасность

### 11.1. Аутентификация и авторизация
```python
class SecurityConfig:
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Scopes
    SCOPES = {
        "read": "Read access",
        "write": "Write access",
        "admin": "Admin access"
    }

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """JWT валидация"""
```

### 11.2. Rate limiting
```python
# Простой rate limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/generate/manual")
@limiter.limit("10/minute")
async def generate_manual_tests(
    request: Request,
    body: ManualTestRequest
):
    """Ограничение: 10 запросов в минуту"""
```

## 12. Мониторинг и логирование

### 12.1. Структурированное логирование
```python
# Настройка structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### 12.2. Метрики
```python
# Prometheus метрики
REQUEST_COUNT = Counter(
    "testops_requests_total",
    "Total requests",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "testops_request_duration_seconds",
    "Request duration"
)

AI_RESPONSE_TIME = Histogram(
    "testops_ai_response_time",
    "AI service response time",
    ["model", "type"]
)
```

## 13. Тестирование

### 13.1. Unit тесты
```python
# Тесты сервисов
@pytest.mark.asyncio
async def test_ai_service_generate_code():
    service = AIService()
    code = await service.generate_code("Test login functionality")
    assert "@allure.feature" in code
    assert "def test_" in code

# Тесты API
async def test_generate_manual_tests(client):
    response = await client.post(
        "/api/v1/generate/manual",
        json={"requirements": "Test user login"}
    )
    assert response.status_code == 200
    assert "code" in response.json()
```

### 13.2. Интеграционные тесты
```python
@pytest.mark.integration
async def test_full_workflow():
    """Тест полного цикла: генерация -> валидация -> GitLab"""
    # 1. Генерация тестов
    # 2. Валидация кода
    # 3. Создание MR в GitLab
```

## 14. Деплой и эксплуатация

### 14.1. Конфигурация
```python
# .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
REDIS_URL=redis://localhost:6380
CLOUD_API_KEY=your_api_key
GITLAB_TOKEN=your_gitlab_token
GITLAB_URL=https://gitlab.example.com
SECRET_KEY=your_secret_key
```

### 14.2. Docker
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 14.3. Health checks
```python
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": settings.VERSION
    }

@app.get("/health/ready")
async def readiness_check():
    """Проверка готовности к работе"""
    db_status = await check_database()
    ai_status = await check_ai_service()

    return {
        "database": db_status,
        "ai_service": ai_status,
        "ready": db_status and ai_status
    }
```

## 15. Документация API

- OpenAPI 3.0 спецификация автоматически генерируется FastAPI
- Примеры запросов/ответов
- Swagger UI на /docs
- ReDoc на /redoc