# Система аутентификации и авторизации

Это backend-приложение реализует собственную систему аутентификации и авторизации с использованием Django REST Framework.

## Особенности реализации

- **Кастомная система аутентификации**: Не используется стандартная Django аутентификация
- **JWT токены**: Для идентификации пользователей используются JWT токены
- **Ролевая модель доступа**: Гибкая система ролей и правил доступа
- **Гранулярные права**: Разграничение прав на чтение/создание/обновление/удаление
- **Разделение прав**: Права на свои объекты vs права на все объекты

## Технологический стек

- Django 4.2.7
- Django REST Framework 3.14.0
- SQLite (вместо PostgreSQL для простоты развертывания)
- JWT (PyJWT)
- bcrypt для хеширования паролей

## Структура проекта

```
test_task/
├── authentication/          # Основное приложение аутентификации
│   ├── models.py           # Модели пользователей, ролей, правил доступа
│   ├── views.py            # API эндпоинты
│   ├── serializers.py      # Сериализаторы DRF
│   ├── authentication.py   # JWT аутентификация
│   ├── authorization.py    # Система проверки прав доступа
│   ├── utils.py            # Утилиты для работы с JWT
│   ├── middleware.py       # Middleware для аутентификации и авторизации
│   └── management/commands/init_data.py  # Инициализация тестовых данных
├── mock_business/          # Mock приложение для демонстрации
│   └── views.py           # Mock бизнес-объекты
├── test_task/              # Основные настройки Django
├── DATABASE_SCHEMA.md      # Описание схемы базы данных
└── requirements.txt        # Зависимости
```

## Установка и запуск

1. Установка зависимостей:
```bash
pip install -r requirements.txt
```

2. Применение миграций:
```bash
python manage.py migrate
```

3. Инициализация тестовых данных:
```bash
python manage.py init_data
```

4. Запуск сервера:
```bash
python manage.py runserver
```

## API Эндпоинты

### Аутентификация пользователей

- `POST /api/auth/register/` - Регистрация нового пользователя
- `POST /api/auth/login/` - Вход в систему
- `POST /api/auth/logout/` - Выход из системы
- `GET /api/auth/profile/` - Просмотр профиля
- `PUT/PATCH /api/auth/profile/` - Обновление профиля
- `DELETE /api/auth/delete-account/` - Мягкое удаление аккаунта
- `GET /api/auth/permissions/` - Просмотр прав текущего пользователя

### Admin API (управление ролями и правами)

- `GET/POST /api/auth/admin/roles/` - Список/создание ролей
- `GET/PUT/DELETE /api/auth/admin/roles/{id}/` - Управление ролью
- `GET/POST /api/auth/admin/business-elements/` - Список/создание бизнес-элементов
- `GET/POST /api/auth/admin/access-rules/` - Список/создание правил доступа
- `GET/PUT/DELETE /api/auth/admin/access-rules/{id}/` - Управление правилами
- `GET/POST /api/auth/admin/user-roles/` - Список/назначение ролей
- `GET/DELETE /api/auth/admin/user-roles/{id}/` - Управление ролями пользователей

### Mock бизнес-объекты

- `GET /api/business/products/` - Список продуктов
- `POST /api/business/products/create/` - Создание продукта
- `GET /api/business/orders/` - Список заказов
- `POST /api/business/orders/create/` - Создание заказа
- `GET /api/business/shops/` - Список магазинов
- `POST /api/business/shops/create/` - Создание магазина
- `GET /api/business/users/` - Список пользователей
- `GET /api/business/reports/` - Отчеты

## Тестовые пользователи

После инициализации данных создаются следующие тестовые пользователи:

1. **Администратор**
   - Email: `admin@example.com`
   - Пароль: `admin123`
   - Права: Полный доступ ко всем ресурсам

2. **Менеджер**
   - Email: `manager@example.com`
   - Пароль: `manager123`
   - Права: Расширенные права на бизнес-объекты

3. **Обычный пользователь**
   - Email: `user@example.com`
   - Пароль: `user123`
   - Права: Базовые права на свои объекты

## Примеры использования

### Регистрация пользователя

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "first_name": "Иван",
    "last_name": "Иванов",
    "patronymic": "Иванович",
    "password": "password123",
    "password_confirm": "password123"
  }'
```

### Вход в систему

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "user123"
  }'
```

### Доступ к защищенному ресурсу

```bash
# С токеном из ответа логина
curl -X GET http://localhost:8000/api/business/products/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Система прав доступа

### Роли

1. **admin**: Полные права на все ресурсы
2. **manager**: Расширенные права на бизнес-объекты
3. **user**: Права на свои объекты
4. **guest**: Минимальные права на чтение публичных данных

### Типы прав

- `read`: Чтение своих объектов
- `read_all`: Чтение всех объектов
- `create`: Создание объектов
- `update`: Обновление своих объектов
- `update_all`: Обновление всех объектов
- `delete`: Удаление своих объектов
- `delete_all`: Удаление всех объектов

### Логика проверки прав

1. **Аутентификация**: Проверка JWT токена
2. **Авторизация**: Проверка прав на основе ролей
3. **Владение**: Проверка владельца объекта (если применимо)

## Особенности реализации

### JWT Аутентификация

- Используются JWT токены с payload: `user_id`, `jti`, `exp`, `iat`
- Сессии хранятся в базе данных для возможности отзыва токенов
- Middleware автоматически аутентифицирует пользователя по токену

### Кастомная модель пользователя

- Расширенная модель User с полями: email, first_name, last_name, patronymic
- Пароли хешируются с использованием bcrypt
- Поддержка мягкого удаления (is_active=False)

### Гибкая система авторизации

- Роли могут иметь разные права на разные бизнес-элементы
- Поддержка разграничения прав на свои vs все объекты
- Кастомные permission классы для DRF
- Middleware для автоматической проверки прав

## Ошибки

- **401 Unauthorized**: Токен отсутствует или невалиден
- **403 Forbidden**: Пользователь аутентифицирован, но нет прав на ресурс
- **400 Bad Request**: Некорректные данные запроса
- **422 Unprocessable Entity**: Ошибка валидации данных

## Административный интерфейс

Доступ к админке: `http://localhost:8000/admin/`

Для входа можно использовать тестового администратора:
- Email: `admin@example.com`
- Пароль: `admin123`
