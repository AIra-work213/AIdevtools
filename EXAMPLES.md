# 🎯 Примеры использования AIdevtools

Коллекция примеров запросов для каждой вкладки, демонстрирующих все возможности проекта.

---

## 📊 Dashboard (Главная)

**Назначение:** Обзор системы, статистика генерации тестов

**Что посмотреть:**
- Общее количество сгенерированных тестов
- Последние 5 генераций
- Графики по типам тестов (Manual, API, UI)
- Средняя скорость генерации

---

## 💬 Chat (AI Ассистент)

**Демонстрация возможностей:**

### Пример 1: Генерация сложных тестовых сценариев
```
Создай автотесты на pytest с Allure для этого REST API системы управления заказами:

КОД API (FastAPI):
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

app = FastAPI()

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItem(BaseModel):
    product_id: int
    quantity: int
    price: float

class Order(BaseModel):
    id: Optional[int] = None
    user_id: int
    items: List[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    total: Optional[float] = None
    created_at: Optional[datetime] = None

orders_db = []

@app.post("/orders", status_code=201)
async def create_order(order: Order):
    order.id = len(orders_db) + 1
    order.total = sum(item.price * item.quantity for item in order.items)
    order.created_at = datetime.now()
    orders_db.append(order.dict())
    return order

@app.get("/orders")
async def get_orders(user_id: Optional[int] = None):
    if user_id:
        return [o for o in orders_db if o["user_id"] == user_id]
    return orders_db

@app.patch("/orders/{order_id}/status")
async def update_status(order_id: int, status: OrderStatus):
    for order in orders_db:
        if order["id"] == order_id:
            if order["status"] == OrderStatus.CANCELLED:
                raise HTTPException(400, "Cannot update cancelled order")
            order["status"] = status
            return order
    raise HTTPException(404, "Order not found")

@app.delete("/orders/{order_id}")
async def cancel_order(order_id: int):
    for order in orders_db:
        if order["id"] == order_id:
            if order["status"] == OrderStatus.DELIVERED:
                raise HTTPException(400, "Cannot cancel delivered order")
            order["status"] = OrderStatus.CANCELLED
            return {"message": "Order cancelled"}
    raise HTTPException(404, "Order not found")

ЗАДАЧА:
Создай полные автотесты с Allure для всех эндпоинтов.
Включи:
- Позитивные сценарии (создание, получение, обновление)
- Негативные (несуществующий ID, невалидный статус, бизнес-правила)
- Валидацию данных (пустые items, отрицательные цены)
- Фикстуры для подготовки тестовых данных
```

### Пример 2: Тесты с БД и моками
```
Напиши тесты для этого сервиса пользователей:

КОД (user_service.py):
from typing import Optional
from datetime import datetime
import hashlib
import secrets
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import User
from email_client import EmailClient

class UserService:
    def __init__(self, db: Session, email_client: EmailClient):
        self.db = db
        self.email_client = email_client
    
    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${pwd_hash}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        salt, pwd_hash = stored_hash.split('$')
        return pwd_hash == hashlib.sha256((password + salt).encode()).hexdigest()
    
    def register_user(self, username: str, email: str, password: str) -> User:
        # Check email uniqueness
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("Email already registered")
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            created_at=datetime.now(),
            is_active=False
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Username already exists")
        
        # Send verification email
        token = secrets.token_urlsafe(32)
        self.email_client.send_verification_email(user.email, token)
        
        return user
    
    def create_auth_token(self, user_id: int) -> str:
        return secrets.token_urlsafe(32)

КОД (models.py):
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)

ЗАДАЧА:
Создай pytest тесты с использованием:
- SQLAlchemy с PostgreSQL (используй pytest-postgresql)
- pytest-mock для мокирования EmailClient
- Транзакции для изоляции тестов
- Тесты всех методов (hash_password, verify_password, register_user, create_auth_token)
- Негативные сценарии (дубликат email/username)
- Проверка отправки email
```

### Пример 3: Асинхронные тесты
```
Создай асинхронные тесты для этого FastAPI эндпоинта:

КОД (file_upload.py):
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
import aiofiles
import os
from pathlib import Path

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

async def validate_image(file: UploadFile) -> bool:
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Invalid file type. Allowed: {ALLOWED_EXTENSIONS}")
    
    # Check size
    content = await file.read()
    await file.seek(0)  # Reset file pointer
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Max: {MAX_FILE_SIZE} bytes")
    
    return True

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    await validate_image(file)
    
    file_path = UPLOAD_DIR / file.filename
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return {
        "filename": file.filename,
        "size": len(content),
        "path": str(file_path)
    }

@app.post("/upload-multiple")
async def upload_multiple(files: List[UploadFile] = File(...)):
    if len(files) > 10:
        raise HTTPException(400, "Maximum 10 files allowed")
    
    results = []
    for file in files:
        await validate_image(file)
        file_path = UPLOAD_DIR / file.filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        results.append({
            "filename": file.filename,
            "size": len(content)
        })
    
    return {"files": results, "total": len(results)}

ЗАДАЧА:
Создай асинхронные тесты с pytest-asyncio и httpx.AsyncClient:
- Загрузка одного изображения (jpg, png)
- Загрузка нескольких файлов одновременно (2-5 файлов)
- Валидация формата (попытка загрузить .txt, .pdf)
- Проверка лимита размера (загрузить файл >5MB)
- Проверка лимита количества (загрузить 11 файлов)
- Используй фикстуры для создания тестовых файлов
- Cleanup после тестов (удаление загруженных файлов)
```

**После генерации:**
- Нажми кнопку "Запустить код" ⚡
- Увидишь Allure отчет с детальной статистикой
- Проверь разбивку по severity (Critical/High/Normal)

---

## 📝 Manual Tests (Ручные тесты)

**Демонстрация возможностей:**

### Пример 1: Тесты для e-commerce (покажет детальность)
```
СИСТЕМА: Интернет-магазин электроники "TechShop"

ОПИСАНИЕ ФУНКЦИОНАЛЬНОСТИ:

1. КАТАЛОГ ТОВАРОВ
   - База: 1000+ товаров (ноутбуки, телефоны, планшеты, аксессуары)
   - Фильтры:
     * Категория (многоуровневая: Электроника → Ноутбуки → Игровые)
     * Цена (слайдер от 0 до 500000₽)
     * Бренд (чекбоксы: Apple, Samsung, Lenovo, HP, Dell)
     * Рейтинг (от 1 до 5 звезд)
     * Наличие (в наличии / под заказ)
   - Сортировка: по цене, рейтингу, новизне, популярности
   - Пагинация: 20 товаров на страницу

2. КОРЗИНА ПОКУПОК
   - Добавление товара (кнопка "В корзину")
   - Изменение количества (input + кнопки +/-)
   - Удаление товара (иконка корзины)
   - Расчет итоговой суммы (товары + доставка)
   - Применение промокодов (скидка 5-50%)
   - Сохранение корзины в localStorage
   - Ограничения:
     * Минимальный заказ: 500₽
     * Максимум 99 шт одного товара
     * Всего максимум 50 позиций в корзине

3. ОФОРМЛЕНИЕ ЗАКАЗА
   - Форма доставки:
     * Город (автодополнение из КЛАДР)
     * Адрес (улица, дом, квартира)
     * Способ: курьер (300₽) / самовывоз (бесплатно) / почта (от 250₽)
   - Форма оплаты:
     * Наличными курьеру
     * Картой онлайн (Сбербанк, Тинькофф)
     * Apple Pay / Google Pay
     * Кредит (Тинькофф, Альфа-Банк)
   - Промокоды:
     * WELCOME10 - скидка 10% для новых
     * SAVE500 - скидка 500₽ при заказе от 5000₽
     * TECH20 - скидка 20% на технику
   - Валидация:
     * Все поля обязательны
     * Email проверяется regex
     * Телефон: формат +7 (XXX) XXX-XX-XX
     * Промокод: проверка валидности и условий

4. ЛИЧНЫЙ КАБИНЕТ
   - История заказов (последние 50, пагинация)
   - Фильтр по статусу (все / в обработке / доставлено / отменено)
   - Детали заказа (товары, сумма, трек-номер)
   - Избранное (до 100 товаров)
   - Отзывы (оценка 1-5 звезд + текст)
   - Редактирование профиля (имя, email, телефон, адреса)

5. ПОИСК
   - Поле поиска в шапке сайта
   - Автодополнение (показывает 5 подсказок)
   - Поиск по названию, бренду, артикулу
   - Подсветка найденных слов в результатах
   - Фильтры применимы к результатам поиска
   - История поиска (последние 10 запросов)

ЗАДАЧА:
Создай детальные тест-кейсы с использованием паттерна AAA (Arrange-Act-Assert).
Включи:
- Позитивные сценарии (happy path)
- Негативные сценарии (невалидные данные, граничные значения)
- Edge cases (пустая корзина, максимальное количество)
- Проверку всех валидаций
- Тестирование промокодов
- Интеграцию между модулями (корзина → оформление → заказ)

Используй Allure декораторы с правильными severity:
- CRITICAL: оплата, оформление заказа
- HIGH: корзина, промокоды
- NORMAL: фильтры, сортировка, поиск
```

**Настройки:**
- Detail Level: `Detailed` (максимальная детализация)
- Test Type: `Functional`
- Include Negative Tests: ✅
- Use AAA Pattern: ✅

**Ожидаемый результат:**
- 20-30 тест-кейсов с Allure декораторами
- Разные severity: Critical (оплата), High (корзина), Normal (фильтры)
- Каждый тест с шагами Arrange-Act-Assert
- Возможность запустить и увидеть Allure отчет

### Пример 2: Интеграционные тесты (покажет сложность)
```
СИСТЕМА: Онлайн-бронирование отелей "BookingPro"

АРХИТЕКТУРА И ИНТЕГРАЦИИ:

1. ОСНОВНОЕ ПРИЛОЖЕНИЕ (Backend: FastAPI + PostgreSQL)
   - API endpoints для поиска, бронирования
   - База данных: отели, номера, бронирования, пользователи
   - Кэширование: Redis для результатов поиска

2. ПЛАТЕЖНАЯ СИСТЕМА (Интеграция с Stripe)
   - Создание платежного намерения (Payment Intent)
   - 3D Secure аутентификация
   - Вебхуки для подтверждения оплаты
   - Возвраты и отмены платежей
   - Тестовые карты:
     * 4242 4242 4242 4242 - успешная оплата
     * 4000 0000 0000 0002 - отклонена банком
     * 4000 0000 0000 9995 - insufficient funds

3. EMAIL СЕРВИС (SendGrid)
   - Подтверждение бронирования (HTML шаблон)
   - Напоминание за 24 часа до заезда
   - Отмена бронирования
   - Счет/квитанция
   - Webhook для отслеживания доставки

4. КАЛЕНДАРЬ (Google Calendar API)
   - Создание события при бронировании
   - Напоминание за день до заезда
   - Синхронизация с личным календарем
   - OAuth 2.0 авторизация

5. SMS УВЕДОМЛЕНИЯ (Twilio)
   - Код подтверждения при регистрации
   - Подтверждение бронирования (номер брони)
   - Напоминание о заезде

БИЗНЕС-ПРОЦЕСС:

1. ПОИСК ОТЕЛЕЙ
   Input: город, даты заезда/выезда, количество гостей
   Процесс:
   - Запрос к БД (фильтр по доступности)
   - Проверка Redis кэша (TTL 5 минут)
   - Расчет цены с учетом количества ночей
   - Применение сезонных коэффициентов
   Output: список отелей с доступными номерами

2. СОЗДАНИЕ БРОНИРОВАНИЯ
   Input: отель, номер, даты, данные гостя
   Процесс:
   - Проверка доступности (БД транзакция)
   - Создание записи бронирования (статус: pending)
   - Резервация номера на 15 минут
   - Создание Payment Intent в Stripe
   - Отправка ссылки на оплату пользователю
   Output: booking_id, payment_url

3. ОПЛАТА
   Input: payment_intent_id, карта
   Процесс:
   - Stripe обрабатывает платеж
   - 3D Secure (если требуется)
   - Webhook: payment_intent.succeeded
   - Обновление статуса: pending → confirmed
   - Списание номера из доступных
   - Отправка email с подтверждением (SendGrid)
   - Отправка SMS с номером брони (Twilio)
   - Создание события в Google Calendar
   Output: booking_confirmed

4. ОТМЕНА БРОНИРОВАНИЯ
   Input: booking_id, причина
   Процесс:
   - Проверка политики отмены (за сколько дней до заезда)
   - Расчет суммы возврата (100% / 50% / 0%)
   - Создание Refund в Stripe
   - Обновление статуса: confirmed → cancelled
   - Возврат номера в доступные
   - Email уведомление об отмене
   - Удаление события из календаря
   Output: refund_amount, refund_id

ИНТЕГРАЦИОННЫЕ СЦЕНАРИИ ДЛЯ ТЕСТИРОВАНИЯ:

1. Happy Path:
   Поиск → Бронирование → Оплата → Email → SMS → Calendar → Заезд

2. Partial Failures:
   - Платеж прошел, но email не отправился
   - Платеж прошел, но Calendar API недоступен
   - Stripe вебхук пришел с задержкой

3. Rollback Scenarios:
   - Платеж отклонен → отмена резервации номера
   - Timeout при 3D Secure → pending истек (15 мин)

4. Edge Cases:
   - Двойное бронирование одного номера (race condition)
   - Отмена во время обработки платежа
   - Изменение цены между поиском и оплатой

ЗАДАЧА:
Создай интеграционные тесты, покрывающие:
- Полные E2E сценарии с реальными API (Stripe test mode, SendGrid sandbox)
- Моки для календаря (Google Calendar API)
- Проверку consistency между системами
- Обработку ошибок интеграций
- Retry логику и идемпотентность
- Webhook processing
- Транзакционность БД

Используй:
- pytest-postgresql для тестовой БД
- fakeredis для кэша
- respx для моков HTTP запросов
- pytest-vcr для записи/воспроизведения API вызовов
- Allure для отчетности с severity по критичности интеграции
```

---

## 🔌 API Tests (Генерация из OpenAPI)

**Демонстрация возможностей:**

### Пример 1: Swagger Petstore (покажет базовую генерацию)
```yaml
openapi: 3.0.0
info:
  title: Pet Store API
  version: 1.0.0
servers:
  - url: https://petstore.swagger.io/v2
paths:
  /pet:
    post:
      summary: Add a new pet
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                status:
                  type: string
                  enum: [available, pending, sold]
      responses:
        200:
          description: Successful
        405:
          description: Invalid input
    get:
      summary: Find pets by status
      parameters:
        - name: status
          in: query
          schema:
            type: string
      responses:
        200:
          description: Successful
  /pet/{petId}:
    get:
      summary: Find pet by ID
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
      responses:
        200:
          description: Successful
        404:
          description: Pet not found
    put:
      summary: Update pet
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                status:
                  type: string
      responses:
        200:
          description: Successful
        404:
          description: Pet not found
    delete:
      summary: Delete pet
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
      responses:
        200:
          description: Successful
        404:
          description: Pet not found
```

**После генерации:**
- Нажми "Запустить тесты" 🎯
- Увидишь тесты для всех endpoints (POST, GET, PUT, DELETE)
- Позитивные сценарии (200) + негативные (404, 405)
- Allure отчет с группировкой по endpoints

### Пример 2: Сложный API с аутентификацией (покажет продвинутые возможности)
```yaml
openapi: 3.0.0
info:
  title: Banking API
  version: 2.0.0
servers:
  - url: https://api.bank.example.com/v2
security:
  - bearerAuth: []
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    Account:
      type: object
      properties:
        id:
          type: string
          format: uuid
        balance:
          type: number
          format: double
        currency:
          type: string
          enum: [USD, EUR, RUB]
paths:
  /auth/login:
    post:
      summary: User login
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                username:
                  type: string
                password:
                  type: string
      responses:
        200:
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  token:
                    type: string
        401:
          description: Invalid credentials
  /accounts:
    get:
      summary: Get user accounts
      responses:
        200:
          description: List of accounts
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Account'
        401:
          description: Unauthorized
  /accounts/{accountId}/transfer:
    post:
      summary: Transfer money
      parameters:
        - name: accountId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                to_account:
                  type: string
                amount:
                  type: number
                  minimum: 0.01
                  maximum: 1000000
                description:
                  type: string
      responses:
        200:
          description: Transfer successful
        400:
          description: Invalid amount
        401:
          description: Unauthorized
        403:
          description: Insufficient funds
        404:
          description: Account not found
```

**Ожидаемый результат:**
- Тесты для аутентификации (JWT токены)
- Тесты для всех CRUD операций
- Валидация граничных значений (amount: 0.01 - 1000000)
- Проверка всех кодов ошибок (400, 401, 403, 404)

---

## 🎨 UI Tests (Генерация из HTML/URL)

**Демонстрация возможностей:**

### Пример 1: URL с адаптивным анализом (самая крутая фича! 🚀)
```
URL: https://www.python.org
Framework: Selenium
```

**Что произойдет:**
1. **Stage 0:** Система просканирует сайт и найдет ~10-15 страниц:
   - https://www.python.org/
   - https://www.python.org/downloads/
   - https://www.python.org/about/
   - https://www.python.org/doc/
   - https://www.python.org/community/
   - и т.д.

2. **Stage 1:** Сгенерирует тесты для КАЖДОЙ страницы:
   - Тест главной страницы (навигация, поиск)
   - Тест страницы Downloads (ссылки на версии)
   - Тест страницы About (контент)
   - Межстраничная навигация

3. **Stage 2:** Обернет все в Allure декораторы

**Результат:**
- Полное покрытие всего сайта, а не только главной страницы
- Специфичные тесты для каждой страницы
- Блок "🎯 Адаптивная генерация: найдено страниц - 12"
- Список всех обнаруженных URL

### Пример 2: Playwright для сложной формы (покажет детальность)
```
URL: https://demoqa.com/automation-practice-form
Framework: Playwright
```

**Ожидаемый результат:**
- Тесты заполнения формы (First Name, Last Name, Email)
- Выбор радио-кнопок (Gender)
- Выбор даты (Date of Birth)
- Загрузка файла (Picture)
- Выбор из выпадающего списка (State, City)
- Submit и проверка модального окна
- Все с Allure steps и скриншотами

### Пример 3: HTML для лендинга (покажет парсинг HTML)
```html
<!DOCTYPE html>
<html>
<head>
    <title>Product Landing Page</title>
</head>
<body>
    <header>
        <nav id="navbar">
            <a href="#home" class="nav-link">Home</a>
            <a href="#features" class="nav-link">Features</a>
            <a href="#pricing" class="nav-link">Pricing</a>
            <a href="#contact" class="nav-link">Contact</a>
        </nav>
    </header>

    <section id="hero">
        <h1>Revolutionary Product</h1>
        <p>Transform your workflow today</p>
        <button id="cta-button" class="btn-primary">Get Started</button>
    </section>

    <section id="features">
        <div class="feature-card" data-feature="speed">
            <h3>Lightning Fast</h3>
            <p>10x faster than competitors</p>
        </div>
        <div class="feature-card" data-feature="secure">
            <h3>100% Secure</h3>
            <p>Bank-level encryption</p>
        </div>
        <div class="feature-card" data-feature="support">
            <h3>24/7 Support</h3>
            <p>Always here to help</p>
        </div>
    </section>

    <section id="pricing">
        <div class="pricing-card" data-plan="basic">
            <h3>Basic</h3>
            <p class="price">$9/month</p>
            <button class="btn-select" data-plan-id="basic">Select Plan</button>
        </div>
        <div class="pricing-card" data-plan="pro">
            <h3>Pro</h3>
            <p class="price">$29/month</p>
            <button class="btn-select" data-plan-id="pro">Select Plan</button>
        </div>
    </section>

    <section id="contact">
        <form id="contact-form">
            <input type="text" id="name" name="name" placeholder="Your Name" required>
            <input type="email" id="email" name="email" placeholder="Your Email" required>
            <textarea id="message" name="message" placeholder="Your Message" required></textarea>
            <button type="submit" id="submit-button">Send Message</button>
        </form>
    </section>

    <footer>
        <p>&copy; 2024 Product Inc.</p>
        <div class="social-links">
            <a href="#" id="twitter-link">Twitter</a>
            <a href="#" id="linkedin-link">LinkedIn</a>
        </div>
    </footer>
</body>
</html>
```

**Framework:** Cypress

**Ожидаемый результат:**
- Тесты навигации (4 ссылки в navbar)
- Тест кнопки CTA
- Тесты карточек фич (3 карточки с data-атрибутами)
- Тесты тарифов (кнопки выбора плана)
- Тест формы контактов (валидация + submit)
- Проверка футера и соцсетей
- Всего ~15-20 тестов для лендинга

---

## 📈 Coverage (Анализ покрытия)

**Демонстрация возможностей:**

### Пример 1: Python модуль с низким покрытием
```python
# calculator.py - КОД ДЛЯ ТЕСТИРОВАНИЯ
class Calculator:
    def add(self, a: int, b: int) -> int:
        """Add two numbers"""
        return a + b
    
    def subtract(self, a: int, b: int) -> int:
        """Subtract b from a"""
        return a - b
    
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers"""
        return a * b
    
    def divide(self, a: int, b: int) -> float:
        """Divide a by b"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def power(self, base: int, exp: int) -> int:
        """Raise base to the power of exp"""
        if exp < 0:
            raise ValueError("Negative exponents not supported")
        result = 1
        for _ in range(exp):
            result *= base
        return result
    
    def factorial(self, n: int) -> int:
        """Calculate factorial of n"""
        if n < 0:
            raise ValueError("Factorial not defined for negative numbers")
        if n == 0 or n == 1:
            return 1
        return n * self.factorial(n - 1)
    
    def is_prime(self, n: int) -> bool:
        """Check if number is prime"""
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True

# СУЩЕСТВУЮЩИЕ ТЕСТЫ (неполные) - test_calculator.py
import pytest
from calculator import Calculator

def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_subtract():
    calc = Calculator()
    assert calc.subtract(5, 3) == 2

# ТЕКУЩЕЕ ПОКРЫТИЕ: ~20% (только 2 из 7 методов)

ЗАДАЧА:
Проанализируй покрытие и создай недостающие тесты для:
- multiply() - базовые случаи
- divide() - нормальное деление + деление на 0 (exception)
- power() - положительные степени + негативная степень (exception) + 0 в степени 0
- factorial() - 0, 1, 5, 10 + негативное число (exception)
- is_prime() - 0, 1, 2, простые (7, 13), составные (4, 9, 15)

Цель: достичь 100% покрытия с Allure декораторами.
```

### Пример 2: FastAPI эндпоинт (покажет API покрытие)
```python
# main.py - КОД API
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

app = FastAPI()

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: EmailStr
    created_at: Optional[datetime] = None

users_db = []

@app.get("/users", response_model=List[User])
async def get_users(skip: int = 0, limit: int = 10):
    """Get list of users with pagination"""
    return users_db[skip:skip + limit]

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get user by ID"""
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users", response_model=User, status_code=201)
async def create_user(user: User):
    """Create new user"""
    # Check if username already exists
    if any(u["username"] == user.username for u in users_db):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user.id = len(users_db) + 1
    user.created_at = datetime.now()
    users_db.append(user.dict())
    return user

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: User):
    """Update existing user"""
    for idx, u in enumerate(users_db):
        if u["id"] == user_id:
            user.id = user_id
            users_db[idx] = user.dict()
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int):
    """Delete user"""
    for idx, u in enumerate(users_db):
        if u["id"] == user_id:
            users_db.pop(idx)
            return
    raise HTTPException(status_code=404, detail="User not found")

# СУЩЕСТВУЮЩИЕ ТЕСТЫ (частичные) - test_main.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/users", json={
            "username": "testuser",
            "email": "test@example.com"
        })
        assert response.status_code == 201

# ТЕКУЩЕЕ ПОКРЫТИЕ: ~15% (только 1 тест из 5 эндпоинтов)

ЗАДАЧА:
Проанализируй покрытие API и создай недостающие тесты:

GET /users:
- Пустой список
- Список с пользователями
- Пагинация (skip=0, limit=5)
- Граничные значения (skip > len(users))

GET /users/{id}:
- Существующий пользователь (200)
- Несуществующий ID (404)

POST /users:
- Успешное создание (201) ✅ (уже есть)
- Дубликат username (400)
- Невалидный email (422)

PUT /users/{id}:
- Успешное обновление (200)
- Несуществующий ID (404)
- Невалидные данные (422)

DELETE /users/{id}:
- Успешное удаление (204)
- Несуществующий ID (404)

Используй:
- pytest-asyncio
- httpx.AsyncClient
- Фикстуры для подготовки тестовых пользователей
- Allure декораторы (feature="User API", severity по критичности)

Цель: 100% покрытие всех endpoints и кодов ответа.
```

---

## 📜 History (История генераций)

**Что проверить:**
- Все предыдущие генерации сохранены
- Фильтрация по типу (Manual/API/UI)
- Поиск по тексту
- Кнопка "Повторить" для быстрой регенерации
- Просмотр старых результатов

---

## ⚙️ Settings (Настройки)

**Настройки AI:**
- Model: Claude Sonnet 4.5 (через Cloud.ru Evolution)
- Temperature: 0.3 (баланс креативности/точности)
- Max Tokens: 16000
- Retry Attempts: 4 (для валидации)

**Настройки генерации:**
- Default Language: Python
- Default Framework: pytest
- Include Allure: ✅ (обязательно)
- AAA Pattern: ✅
- Negative Tests: ✅

---

## 🎯 Комплексный сценарий (покажет все возможности)

### Шаг 1: Chat - Генерация базовых тестов
```
Создай pytest тесты для API управления задачами (TODO app):
- Создать задачу (POST /tasks)
- Получить все задачи (GET /tasks)
- Обновить задачу (PUT /tasks/{id})
- Удалить задачу (DELETE /tasks/{id})

Используй Allure, включи валидацию данных.
```
→ Запусти тесты → Увидишь Allure отчет

### Шаг 2: API Tests - OpenAPI для той же системы
```yaml
openapi: 3.0.0
info:
  title: TODO API
  version: 1.0.0
paths:
  /tasks:
    get:
      summary: Get all tasks
      responses:
        200:
          description: Success
    post:
      summary: Create task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                title:
                  type: string
                completed:
                  type: boolean
      responses:
        201:
          description: Created
  /tasks/{id}:
    put:
      summary: Update task
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        200:
          description: Updated
    delete:
      summary: Delete task
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        204:
          description: Deleted
```
→ Сгенерируй → Запусти тесты → Сравни с Chat

### Шаг 3: UI Tests - Фронтенд для TODO
```
URL: https://todomvc.com/examples/react/
Framework: Playwright
```
→ Увидишь адаптивный анализ → Тесты для UI

### Шаг 4: Coverage - Проверь покрытие
Вставь код API + существующие тесты
→ AI предложит улучшения

### Шаг 5: History
→ Посмотри все 4 генерации
→ Сравни результаты

---

## 🌟 Ключевые фишки для демонстрации

1. **Двухэтапная генерация** - сначала логика, потом Allure (покажи в логах)
2. **Адаптивный анализ сайта** - URL → сканирование → тесты для всех страниц
3. **Запуск тестов прямо в UI** - кнопка "Запустить" → Allure отчет
4. **AI retry с 4 попытками** - автоматическое исправление синтаксических ошибок
5. **Покрытие до 50k символов** - большие OpenAPI спецификации
6. **Auto requirements.txt** - автоматическая генерация зависимостей для UI тестов
7. **Multi-framework** - Playwright, Selenium, Cypress для UI
8. **Интеграция с Allure** - каждый тест с декораторами (@allure.feature, @allure.severity)

---

## 💡 Советы

- Используй **детализированные требования** для лучших результатов
- Экспериментируй с **температурой** (0.2 = консервативно, 0.5 = креативно)
- Для UI тестов **всегда используй URL** для адаптивного анализа
- Проверяй **History** для отслеживания эволюции тестов
- **Запускай тесты** после генерации для проверки работоспособности

---

Создано для AIdevtools 🚀
