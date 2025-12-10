# TestOps Copilot 🤖

> ✅ **Статус:** Полностью рабочий и протестирован (24/24 тестов пройдено)
> 🎉 **Обновление (10.12.2025):** Добавлена двухэтапная генерация, Allure отчеты, автоматическая доработка кода, многострочный ввод

Интеллектуальный ассистент для автоматизации рутинных операций QA-инженеров на базе Cloud.ru Evolution Foundation Model (Qwen 3 Coder 480B).

## 🚀 Возможности

### Основные функции
- ✅ **Двухэтапная генерация тестов** - Framework → Allure decorators (НОВОЕ!)
- ✅ **Генерация ручных тестов** из текстовых требований с Allure decorators
- ✅ **Генерация API тестов** из OpenAPI спецификаций
- ✅ **Генерация UI тестов** для Playwright/Selenium
- ✅ **Выполнение кода с Allure отчетами** - pytest + детальная статистика (НОВОЕ!)
- ✅ **Автоматическая доработка кода** - AI retry при ошибках валидации (НОВОЕ!)
- ✅ **Валидация кода** на соответствие стандартам pytest
- ✅ **Поиск дубликатов** в существующих тестах
- ✅ **Интеграция с GitLab** для создания Merge Requests

### UX улучшения
- ✅ **Многострочный ввод** - Shift+Enter для новой строки (НОВОЕ!)
- ✅ **Красивый веб-интерфейс** с тёмной темой и редактором кода
- ✅ **Загрузка файлов** для контекста генерации
- ✅ **JWT Authentication** и rate limiting

## 🎯 Что нового (10.12.2025)

### 1. Двухэтапная генерация
```
User Request → AI Model 1 (pytest) → AI Model 2 (Allure) → Final Code
```
- Stage 1: Генерация чистой логики тестов
- Stage 2: Добавление Allure аннотаций
- Температура адаптируется на каждом этапе

### 2. Allure отчеты в реальном времени
- 📊 Статистика тестов (пройдено/провалено/сломано)
- 📝 Детали каждого теста с временем выполнения
- 🎨 Цветовое кодирование статусов
- 📁 Сохранение JSON отчетов

### 3. Автоматическая доработка
- Валидация → Базовые фиксы → AI retry (2x)
- Исправление синтаксиса, импортов, отступов
- Контекст ошибок передается AI для точного исправления

### 4. Многострочный ввод
- **Enter** - отправка сообщения
- **Shift+Enter** - новая строка
- Auto-resize textarea (до 200px)

📚 Подробности: [CHANGELOG_20251210.md](CHANGELOG_20251210.md) | [QUICKSTART.md](QUICKSTART.md)

## 📋 Требования

- **Python 3.12+** (для backend)
- **Node.js 18+** (для frontend)
- **PostgreSQL** (опционально, для production)
- **Redis** (опционально, для rate limiting)

## 🛠️ Быстрый старт (для разработки)

### 1. Установка зависимостей

**Backend:**
```bash
cd src/backend
python -m venv ../../.venv
source ../../.venv/bin/activate  # Linux/Mac
# или
../../.venv\Scripts\activate  # Windows

pip install -r requirements.txt  # Теперь включает allure-pytest
```

**Frontend:**
```bash
cd src/frontend
npm install
```

### 2. Настройка окружения

Создайте `.env` файл в корне проекта:
```bash
cp .env.example .env
```

**Обязательные параметры:**
```env
# Cloud.ru API
CLOUD_API_KEY=your_api_key_here

# JWT Secret
SECRET_KEY=your_super_secret_key_here

# Database (PostgreSQL)
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=testops_copilot

# GitLab Integration
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=your_gitlab_token
```

### 3. Запуск сервисов

**Backend (Terminal 1):**
```bash
cd src/backend
source ../../.venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend (Terminal 2):**
```bash
cd src/frontend
npm run dev
```

### 4. Доступ к приложению

- 🌐 **Frontend:** http://localhost:3001
- 🔧 **Backend API:** http://localhost:8001
- 📚 **API Docs:** http://localhost:8001/docs
- ❤️ **Health Check:** http://localhost:8001/health

## 🧪 Тестирование

### Backend тесты
```bash
cd src/backend
source ../../.venv/bin/activate
pytest tests/ -v
```

### Frontend тесты
```bash
cd src/frontend
npm test
```

### Интеграционные тесты
```bash
chmod +x test_integration.sh
./test_integration.sh
```

**Результаты:**
- ✅ Backend: 10/10 тестов
- ✅ Frontend: 14/14 тестов
- ✅ Integration: 5/5 проверок
- Grafana: http://localhost:3002 (admin/admin)

## 🧪 Запуск тестов

### Backend тесты
```bash
# Перейдите в директорию backend
cd src/backend

# Установите зависимости
pip install -r requirements.txt
pip install -r requirements-test.txt

# Запустите тесты
pytest tests/ -v

# Запустите тесты с покрытием
pytest tests/ -v --cov=src --cov-report=html

# Запустите конкретные тесты
pytest tests/test_api/test_generate.py -v
```

### Frontend тесты
```bash
# Перейдите в директорию frontend
cd src/frontend

# Установите зависимости
npm ci

# Запустите unit тесты
npm test

# Запустите тесты в watch режиме
npm run test:watch

# Запустите E2E тесты
npm run test:e2e
```

### Все тесты вместе
```bash
# Запуск всех тестов через скрипт
./scripts/run-all-tests.sh
```

## 📦 Структура проекта

```
testops-copilot/
├── src/
│   ├── backend/          # FastAPI бэкенд
│   │   ├── app/         # Исходный код
│   │   └── tests/       # Тесты
│   ├── frontend/        # React фронтенд
│   │   ├── src/         # Исходный код
│   │   └── tests/       # Тесты
│   └── ai-core/         # ML/AI модуль
├── tests/               # E2E тесты
├── scripts/             # Вспомогательные скрипты
├── docker-compose.yml   # Docker конфигурация
└── README.md
```

## 🔧 Локальная разработка

### Backend
```bash
cd src/backend

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Установите зависимости
pip install -r requirements.txt

# Запустите миграции
alembic upgrade head

# Запустите сервер
uvicorn app.main:app --reload
```

### Frontend
```bash
cd src/frontend

# Установите зависимости
npm install

# Запустите dev сервер
npm run dev
```

### AI Core Module
```bash
cd src/ai-core

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Запустите тест генерации
python -m generation.manual_tests
```

## 📊 Использование

### 1. Генерация ручных тестов

1. Откройте http://localhost:3001
2. Перейдите в раздел "Чат с ассистентом"
3. Введите требования:
   ```
   User should be able to:
   - Login with valid credentials
   - See error with invalid password
   - Reset password via email
   ```
4. Нажмите "Отправить"
5. Получите сгенерированный код в редакторе справа

### 2. Генерация API тестов

1. В чате выберите тип генерации "API тесты"
2. Загрузите OpenAPI спецификацию или вставьте YAML/JSON
3. Укажите эндпоинты для покрытия
4. Получите готовые pytest тесты

### 3. Валидация кода

1. Вставьте код тестов в чат
2. Выберите действие "Валидировать"
3. Получите отчет об ошибках и предупреждениях

### 4. Интеграция с GitLab

1. Нажмите "Отправить в GitLab"
2. Выберите проект и ветку
3. Система создаст Merge Request с тестами

## 🧪 Пример сгенерированного кода

```python
import allure
import pytest
from allure_commons.types import Severity

@allure.feature("Authentication")
@allure.story("User Login")
@allure.label("owner", "QA Team")
@allure.tag("generated_by_ai")
class TestUserLogin:
    @allure.title("User login with valid credentials")
    @allure.severity(Severity.CRITICAL)
    @allure.manual
    def test_user_login_valid_credentials(self):
        """
        Verify user can login with valid username and password
        """
        with allure.step("Arrange: Open login page"):
            # TODO: Navigate to login page
            pass

        with allure.step("Act: Enter valid credentials"):
            # TODO: Enter username and password
            pass

        with allure.step("Assert: Verify successful login"):
            # TODO: Check user is logged in
            pass
```

## 🔍 Мониторинг

- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3002
  - Логин: admin
  - Пароль: admin

## 📝 Документация API

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 🤝 Внесение вклада

1. Форкните репозиторий
2. Создайте ветку feature (`git checkout -b feature/amazing-feature`)
3. Commit ваши изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл LICENSE для деталей

## 🆘 Поддержка

Если у вас есть вопросы или проблемы, пожалуйста:
1. Проверьте раздел [Issues](https://github.com/your-repo/testops-copilot/issues)
2. Создайте новый issue с подробным описанием

## 🗺️ Дорожная карта

- [ ] Поддержка UI/E2E тестов
- [ ] Интеграция с Jira
- [ ] Мультиязычная поддержка
- [ ] Вебхуки для CI/CD
- [ ] Шаблоны тестов

---

**Авторы**: TestOps Copilot Team

**Специально благодарим**: Cloud.ru за доступ к Evolution Foundation Model