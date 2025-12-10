# 🏗️ TestOps Copilot - Архитектура системы

## Обзор системы

TestOps Copilot - это full-stack приложение для автоматизации QA процессов с использованием ИИ. Система состоит из React фронтенда и FastAPI бэкенда, интегрированного с AI-моделью через CloudEvolutionClient (OpenAI API).

**Стек технологий:**
- Frontend: React 18 + TypeScript + Vite + TailwindCSS
- Backend: FastAPI + Python 3.10 + structlog
- AI: CloudEvolutionClient (OpenAI gpt-oss-120b)
- VCS: GitPython для работы с репозиториями
- Deployment: Docker + GitLab CI/CD

---

## 📋 Реализованные функции

### 1. ИИ Ассистент для генерации тестов

**Frontend: `/chat`**
- **Компонент:** `src/frontend/src/pages/Chat.tsx`
- **Store:** `src/frontend/src/stores/chatStore.ts`

**Что делает:**
1. Предоставляет интерфейс чата для общения с ИИ
2. Поддерживает загрузку файлов (requirements, спецификации)
3. Отображает сгенерированный код в Monaco Editor
4. Сохраняет историю диалогов в localStorage через Zustand
5. Поддерживает настройки генерации (температура, детализация, framework)

**Backend API: `/api/v1/generate`**
- **Эндпоинт:** `src/backend/app/api/v1/endpoints/generate.py`
- **Сервис:** `src/backend/app/services/ai_service.py`

**Обработка запроса:**
```
User Message (Frontend)
    ↓
POST /api/v1/generate/manual
    ↓
AIService.generate_manual_tests()
    ↓
CloudEvolutionClient.chat_completion()
    - Model: openai/gpt-oss-120b
    - Temperature: 0.3-2.0 (настраиваемо)
    - Max tokens: 1000-32000
    - Streaming: НЕТ (фронтенд использует обычный POST, не SSE)
    ↓
Markdown cleanup (remove ```python```)
    ↓
ValidationService.validate_code()
    - Синтаксис (ast.parse)
    - Структурные проверки
    - Metrics (complexity, lines)
    ↓
Response → Frontend
    - code: str (pytest tests)
    - test_cases: List[TestCase]
    - validation: ValidationResult
    - generation_time: float
```

**Поддерживаемые режимы генерации:**
- ✅ `/manual` - Генерация ручных тестов из текстовых требований
- ⚠️ `/manual/stream` - Стриминг генерация (SSE) - **Backend реализован, Frontend не использует**
- ⚠️ `/auto/api` - Генерация API тестов из OpenAPI (реализовано, но не подключено в UI)
- ❌ `/auto/ui` - Генерация UI тестов (заглушка, не реализовано)

---

### 2. Анализ покрытия кода

**Frontend: `/coverage`**
- **Компонент:** `src/frontend/src/pages/Coverage.tsx`
- **Store:** `src/frontend/src/stores/coverageStore.ts`
- **Подкомпоненты:**
  - `CoverageVisualization.tsx` - визуализация метрик
  - `UncoveredFunctionsList.tsx` - список непокрытых функций
  - `GeneratedTestsViewer.tsx` - просмотр/скачивание тестов

**Что делает:**
1. Анализирует GitHub/GitLab репозитории
2. Вычисляет процент покрытия кода тестами
3. Находит непокрытые функции (с цикломатической сложностью)
4. Генерирует тесты для выбранных функций через ИИ
5. Валидирует сгенерированные тесты
6. Позволяет скачать результаты

**Backend API: `/api/v1/coverage`**
- **Эндпоинт:** `src/backend/app/api/v1/endpoints/coverage.py`
- **Сервисы:** 
  - `src/backend/app/services/coverage_service.py`
  - `src/backend/app/services/ai_service.py`
  - `src/backend/app/services/validation_service.py`

**Обработка GitHub репозитория:**
```
POST /api/v1/coverage/upload/github
    - Body: { repo_url, language, framework }
    ↓
CoverageService.upload_from_github()
    ↓
1. Git.clone(repo_url, depth=1, single_branch=True)
    - Shallow clone для скорости
    - Фильтрация бинарных файлов (30+ расширений)
    ↓
2. Обход файлов проекта
    - Поддержка: .py, .js, .ts, .java, .cs и др.
    - Определение кодировки (chardet)
    - Пропуск тестовых файлов
    ↓
3. AST парсинг (для Python)
    ast.parse(source_code)
    ↓
    Извлечение функций:
    - Имя функции
    - Количество строк
    - Параметры
    - Docstring
    - Цикломатическая сложность
    ↓
4. Поиск покрытия
    - Сканирование test_*.py файлов
    - Поиск вызовов функций
    - isinstance() проверки, With/AsyncWith contexts
    ↓
5. Расчет метрик
    coverage = covered_functions / total_functions * 100
    ↓
Response → Frontend
    - total_files: int
    - overall_coverage: float (6.7%)
    - uncovered_functions: List[UncoveredFunction]
        * name, file, lines, complexity, params
    - file_coverage: Dict[str, float]
```

**Генерация тестов для непокрытых функций:**
```
POST /api/v1/coverage/generate-tests
    - Body: { functions: List[UncoveredFunction], language, framework }
    ↓
Для каждой функции:
    AIService.generate_code()
        - Промпт: создание pytest теста
        - Temperature: 0.3 (для стабильности)
        - Max tokens: 2000
        ↓
    CloudEvolutionClient.chat_completion()
        - Генерация ~3400 символов за 10 сек
        ↓
    ValidationService.validate_structure()
        - Проверка: assertions, docstrings, AAA pattern
        - Результат: errors, warnings, suggestions
        ↓
    Преобразование List[Dict] → List[str]
        format_validation_item():
        {"type": "no_assertions", "line": 87}
        → "no_assertions: Test has no assertions (line 87)"
        ↓
Объединение всех тестов
    ↓
Response → Frontend
    - generated_tests: str (полный pytest код)
    - validation: ValidationResult
        * errors: List[str]
        * warnings: List[str]  
        * suggestions: List[str]
```

**Поддерживаемые источники:**
- ✅ GitHub репозитории (через git clone)
- ⚠️ GitLab репозитории (эндпоинт есть, не тестировался)
- ⚠️ Загрузка файлов напрямую (эндпоинт есть, не подключен в UI)

---

### 3. История диалогов

**Frontend: `/history`**
- **Компонент:** `src/frontend/src/pages/History.tsx`
- **Store:** `src/frontend/src/stores/historyStore.ts`

**Что делает:**
1. Отображает список сохраненных диалогов
2. Показывает метаданные (дата создания, количество сообщений)
3. Позволяет загрузить диалог обратно в чат
4. Редактирование названий диалогов
5. Экспорт диалога (JSON, Markdown, Text)
6. Удаление диалогов

**Хранение:**
- **LocalStorage** через Zustand persist middleware
- Десериализация дат при загрузке (onRehydrateStorage)
- Максимум 100 последних диалогов

**Структура данных:**
```typescript
interface ChatHistory {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: Date
  updatedAt: Date
  metadata?: {
    code?: string
    testCases?: any[]
    generationSettings?: any
  }
}
```

**Backend:** ❌ Нет серверного хранения (только клиент)

---

### 4. Настройки генерации

**Frontend: `/settings`**
- **Компонент:** `src/frontend/src/pages/Settings.tsx`
- **Store:** `src/frontend/src/stores/settingsStore.ts`

**Настраиваемые параметры:**
- **Уровень детализации:** minimal | standard | detailed
- **Температура:** 0.0 - 2.0 (креативность AI)
- **Max tokens:** 1000 - 32000
- **Язык по умолчанию:** Python, JS, TS, Java, C#
- **Framework:** pytest, unittest, jest, mocha, etc.
- **AAA паттерн:** включен/выключен
- **Негативные тесты:** включены/выключены
- **Темная тема:** включена/выключена

**Хранение:** LocalStorage через Zustand persist

**Backend:** Не требуется (настройки применяются на клиенте)

---

### 5. Дашборд со статистикой

**Frontend: `/dashboard`**
- **Компонент:** `src/frontend/src/pages/Dashboard.tsx`
- **Подкомпоненты:**
  - `QuickActions.tsx` - кнопки быстрого доступа
  - `RecentActivity.tsx` - последние диалоги

**Реальная статистика (из stores):**
1. **Сгенерировано тестов** - подсчет из metadata всех сообщений
2. **Блоков кода** - количество code в metadata
3. **Сохранено диалогов** - chatHistory.length
4. **Валидаций кода** - подсчет validation в metadata

**Быстрые действия:**
- ИИ Ассистент → `/chat`
- Анализ покрытия → `/coverage`
- История диалогов → `/history`
- Настройки ИИ → `/settings`

**Backend:** Не требуется (агрегация на клиенте)

---

## ⚠️ Частично реализованные функции

### Валидация кода

**Backend API: `/api/v1/analyze/validate`**
- **Эндпоинт:** `src/backend/app/api/v1/endpoints/analyze.py`
- **Сервисы:** 
  - `ValidationService` - структурные проверки
  - `AIService` - AI-валидация

**Что работает:**
- ✅ Проверка синтаксиса Python (ast.parse)
- ✅ Структурный анализ кода
- ✅ Расчет метрик (complexity, lines, functions)
- ✅ AI-powered suggestions

**Что НЕ подключено:**
- ❌ Нет UI для отдельной валидации (только внутри генерации)
- ❌ Не используется в чате напрямую

---
### Поиск дубликатов тестов

**Backend API: `/api/v1/analyze/duplicates`**
- **Эндпоинт:** `src/backend/app/api/v1/endpoints/analyze.py`
- **Сервис:** `DuplicateService`

**Алгоритм:**
1. Токенизация кода тестов
2. Сравнение по edit distance / cosine similarity
3. Группировка похожих тестов

**Статус:** ❌ Реализован backend, нет UI

---

### Стриминг генерация тестов

**Backend API: `/api/v1/generate/manual/stream`**
- **Эндпоинт:** `src/backend/app/api/v1/endpoints/generate.py`
- **Протокол:** Server-Sent Events (SSE)

**Что реализовано:**
- ✅ Streaming response через StreamingResponse
- ✅ Progress updates (started, generating 50%, completed)
- ✅ Error handling в stream
- ✅ Правильные headers (Cache-Control, Connection)

**Что НЕ работает:**
- ❌ Frontend не использует EventSource
- ❌ chatStore.ts использует обычный fetch POST
- ❌ Нет UI для отображения прогресса

**Статус:** ⚠️ Backend полностью реализован, Frontend игнорирует
**Статус:** ❌ Реализован backend, нет UI

---

### GitLab интеграция

**Backend API: `/api/v1/gitlab`**
- **Эндпоинт:** `src/backend/app/api/v1/endpoints/gitlab.py`
- **Сервис:** `GitLabService`

**Функции:**
- `/projects` - список проектов
- `/mr` - создание Merge Request
- `/commit` - коммит файлов
- `/branches/{project_id}` - список веток
- `/upload-and-mr` - загрузка тестов + MR

**Статус:** ⚠️ Backend реализован, не тестировался, нет UI

---

## ❌ Не реализованные функции

### 1. UI тесты (auto/ui)
- Эндпоинт существует как заглушка
- Нет логики генерации

### 2. Оптимизация тестов (/analyze/optimize)
- Эндпоинт существует
- Нет реальной логики

### 3. Метрики проекта (/analyze/metrics)
- Эндпоинт существует
- Возвращает моковые данные

### 4. Аутентификация
- `ProtectedRoute` компонент с заглушкой
- `isAuthenticated = true` всегда
- Нет реального login/signup

### 5. Rate limiting
- `RateLimiter` класс реализован
- Не активирован (всегда пропускает)

---

## 🔄 Поток данных в системе

### Полный цикл генерации тестов через чат:

```
1. User вводит требования в Chat UI
    ↓
2. Frontend: useChatStore.sendMessage()
    - Добавляет user message в локальный state
    - POST /api/v1/generate/manual
    ↓
3. Backend: generate.py → generate_manual_tests()
    - Rate limit check (заглушка)
    - Логирование в structlog
    ↓
4. AIService.generate_manual_tests()
    - Формирование промпта с контекстом
    - Применение generation_settings
    ↓
5. CloudEvolutionClient.chat_completion()
    - API: foundation-models.api.cloud.ru
    - Model: openai/gpt-oss-120b
    - Streaming: нет (full response)
    ↓
6. AI генерирует pytest код
    - ~3400 chars за ~10 сек
    ↓
7. Cleanup markdown (remove ```python```)
    ↓
8. ValidationService.validate_structure()
    - ast.parse для синтаксиса
    - Проверка AAA pattern
    - Проверка assertions
    - Подсчет warnings
    ↓
9. Формирование ManualTestResponse
    - code: str
    - test_cases: List[TestCase]
    - validation: ValidationResult
    - generation_time: float
    ↓
10. Response → Frontend
    ↓
11. useChatStore обновляет state
    - appendMessage(assistant message)
    - setLoading(false)
    ↓
12. UI обновляется
    - ChatInterface показывает ответ
    - CodeEditor отображает код
    ↓
13. Auto-save (опционально)
    - Каждые 30 сек → localStorage
    ↓
14. Manual save
    - User → "Сохранить"
    - useHistoryStore.saveChat()
    - Persist в localStorage
```

### Полный цикл анализа покрытия:

```
1. User вводит GitHub URL в Coverage UI
    ↓
2. Frontend: POST /api/v1/coverage/upload/github
    - repo_url, language, framework
    ↓
3. Backend: coverage.py → upload_from_github()
    ↓
4. CoverageService.clone_repository()
    - git clone --depth 1 --single-branch
    - temp directory
    ↓
5. Фильтрация файлов
    - Пропуск binary (BINARY_EXTENSIONS)
    - Только source (SOURCE_EXTENSIONS)
    ↓
6. Для каждого .py файла:
    - Определение кодировки (chardet)
    - ast.parse()
    - Извлечение ast.FunctionDef
    - Расчет complexity
    ↓
7. Сканирование test_*.py
    - Поиск вызовов функций
    - Маркировка covered
    ↓
8. Расчет метрик
    - overall_coverage = covered/total * 100
    - file_coverage по файлам
    ↓
9. Response → Frontend
    - CoverageAnalysisResponse
    ↓
10. UI отображает:
    - Круговая диаграмма (CoverageVisualization)
    - Список функций (UncoveredFunctionsList)
    ↓
11. User выбирает функции → "Сгенерировать тесты"
    ↓
12. POST /api/v1/coverage/generate-tests
    - functions: List[UncoveredFunction]
    ↓
13. Для каждой функции:
    - AIService.generate_code()
    - ValidationService.validate_structure()
    - format_validation_item() (Dict→str)
    ↓
14. Объединение тестов
    ↓
15. Response → Frontend
    - GenerateTestsForCoverageResponse
    ↓
16. GeneratedTestsViewer
    - Monaco editor
    - Download button
```

---

## 🗂️ Структура проекта

```
AIdevtools/
├── src/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/v1/endpoints/
│   │   │   │   ├── generate.py      # Генерация тестов
│   │   │   │   ├── coverage.py      # Анализ покрытия
│   │   │   │   ├── analyze.py       # Валидация, дубликаты
│   │   │   │   ├── gitlab.py        # GitLab интеграция
│   │   │   │   └── health.py        # Health check
│   │   │   ├── services/
│   │   │   │   ├── ai_service.py            # AI генерация
│   │   │   │   ├── coverage_service.py      # Coverage анализ
│   │   │   │   ├── validation_service.py    # Валидация
│   │   │   │   ├── duplicate_service.py     # Поиск дубликатов
│   │   │   │   └── gitlab_service.py        # GitLab API
│   │   │   ├── schemas/
│   │   │   │   └── test.py          # Pydantic models
│   │   │   ├── core/
│   │   │   │   ├── config.py        # Settings
│   │   │   │   ├── deps.py          # Dependencies
│   │   │   │   └── logging.py       # Structlog setup
│   │   │   └── main.py              # FastAPI app
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── pages/
│       │   │   ├── Dashboard.tsx    # Главная страница
│       │   │   ├── Chat.tsx         # ИИ чат
│       │   │   ├── Coverage.tsx     # Анализ покрытия
│       │   │   ├── History.tsx      # История диалогов
│       │   │   └── Settings.tsx     # Настройки
│       │   ├── components/
│       │   │   ├── chat/            # Компоненты чата
│       │   │   ├── code-coverage/   # Coverage UI
│       │   │   ├── dashboard/       # Dashboard widgets
│       │   │   ├── editor/          # Monaco editor
│       │   │   └── ui/              # UI компоненты
│       │   ├── stores/
│       │   │   ├── chatStore.ts     # Chat state
│       │   │   ├── historyStore.ts  # History state
│       │   │   ├── coverageStore.ts # Coverage state
│       │   │   └── settingsStore.ts # Settings state
│       │   ├── hooks/               # React hooks
│       │   ├── utils/               # Utilities
│       │   └── index.css            # Tailwind styles
│       └── package.json
├── docker-compose.yml
├── .gitlab-ci.yml
└── README.md
```

---

## 🔌 Интеграции

### CloudEvolutionClient (OpenAI API)
- **Эндпоинт:** `foundation-models.api.cloud.ru`
- **Модель:** `openai/gpt-oss-120b`
- **Использование:**
  - Генерация тестов
  - AI-валидация кода
  - Suggestions для улучшения

### GitPython
- **Версия:** 3.1.43
- **Использование:**
  - Clone GitHub репозиториев
  - Shallow clone (depth=1) для производительности

### Structlog
- **Использование:**
  - Структурированное логирование
  - JSON output для production
  - Контекстные логи (user, operation)

---

## 📊 Метрики производительности

### AI генерация тестов:
- Средний размер ответа: ~3400 символов
- Среднее время генерации: ~10 секунд
- Успешность: >95% (при правильных промптах)

### Coverage анализ:
- GitHub clone: ~5-10 сек (зависит от размера)
- AST парсинг: <1 сек для типичного файла
- Общий анализ проекта: 10-30 сек

### Frontend:
- Initial load: ~1 сек
- Page transitions: <100ms
- LocalStorage operations: <10ms

---

## 🚀 Deployment

### Docker
```yaml
services:
  frontend:
    build: ./src/frontend
    ports: ["3001:80"]
    
  backend:
    build: ./src/backend
    ports: ["8001:8000"]
    environment:
      - OPENAI_API_KEY
      - OPENAI_BASE_URL
```

### GitLab CI/CD
```yaml
stages:
  - build
  - deploy

deploy:
  script:
    - docker compose up -d --build
  only:
    - main
```

**Production URL:** http://89.169.132.244:3001

---

## 🔐 Безопасность

### Текущее состояние:
- ❌ Нет реальной аутентификации
- ❌ Нет авторизации
- ⚠️ Rate limiting реализован, но не активен
- ✅ CORS настроен корректно
- ✅ Environment variables для API keys

### TODO:
- Добавить JWT аутентификацию
- Включить rate limiting
- Добавить role-based access control

---

## 📝 Логирование

### Backend (structlog):
```python
logger.info(
    "Generating manual tests",
    user=username,
    requirements_length=len(request.requirements)
)
```

### Production logs:
- Структурированный JSON
- Трейсинг запросов
- Error tracking с exc_info

---

## 🧪 Тестирование

### Backend:
- ❌ Unit тесты не написаны
- ⚠️ Ручное тестирование проведено

### Frontend:
- ❌ Unit тесты не написаны
- ✅ E2E тестирование вручную

---

**Версия:** 1.0.8  
**Последнее обновление:** 10 декабря 2025 г.  
**Статус:** Production (стабильная версия)
