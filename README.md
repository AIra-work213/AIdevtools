# AI Dev Tools

Проект для автоматизации генерации UI тестов с использованием AI.

## Структура проекта

```
.
├── src/
│   ├── ai-core/          # Основной AI функционал
│   ├── backend/          # Backend часть приложения
│   └── frontend/         # Frontend часть приложения
├── test_suite/           # Все тесты и тестовые утилиты
│   ├── frontend_tests/   # Тесты frontend
│   ├── unit/             # Unit тесты
│   ├── integration/      # Интеграционные тесты
│   └── ...
├── docker-compose.yml    # Docker конфигурация
├── requirements.txt      # Python зависимости
└── package.json         # Node.js зависимости
```

## Установка и запуск

### Backend

```bash
cd src/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd src/frontend
npm install
npm run dev
```

### Запуск с Docker

```bash
docker-compose up
```

## Основные возможности

- Генерация UI тестов с помощью AI
- Поддержка различных фреймворков тестирования
- Веб-интерфейс для управления тестами
- Анализ покрытия кода тестами

## Документация

Подробная документация находится в разработке.