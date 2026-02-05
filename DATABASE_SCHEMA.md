# 🗄️ Схема базы данных

## 📋 Обзор

Проект использует SQLite базу данных с двумя основными приложениями:
- `authentication` - система аутентификации и авторизации
- `mock_business` - бизнес-логика маркетплейса

## 🔐 Authentication App

### User (Пользователи)

Основная модель пользователей системы.

```sql
CREATE TABLE authentication_user (
    id UUID PRIMARY KEY,
    email VARCHAR(254) UNIQUE NOT NULL,
    first_name VARCHAR(30),
    last_name VARCHAR(30),
    patronymic VARCHAR(30),
    password_hash VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    ban_until DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Поля:**
- `id` - Уникальный идентификатор пользователя
- `email` - Email адрес (уникальный)
- `first_name` - Имя пользователя
- `last_name` - Фамилия пользователя
- `patronymic` - Отчество пользователя
- `password_hash` - Хеш пароля (bcrypt)
- `is_active` - Активен ли аккаунт
- `is_staff` - Доступ к админ панели
- `is_superuser` - Суперпользователь
- `ban_until` - Дата окончания бана (NULL - без бана)
- `created_at` - Дата создания
- `updated_at` - Дата обновления

**Свойства:**
- `full_name` - Полное имя (фамилия + имя + отчество)
- `is_banned` - Проверка забанен ли пользователь

### Role (Роли)

Система ролей для разграничения доступа.

```sql
CREATE TABLE authentication_role (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Предопределенные роли:**
- `user` - Обычный пользователь
- `manager` - Менеджер магазина
- `admin` - Администратор системы

### UserRole (Связь пользователей и ролей)

Many-to-many связь между пользователями и ролями.

```sql
CREATE TABLE authentication_userrole (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES authentication_user(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES authentication_role(id) ON DELETE CASCADE,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role_id)
);
```

### BusinessElement (Бизнес-элементы)

Элементы системы для разграничения прав доступа.

```sql
CREATE TABLE authentication_businesselement (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    has_owner_field BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Предопределенные элементы:**
- `shops` - Управление магазинами
- `products` - Управление товарами
- `orders` - Управление заказами
- `users` - Управление пользователями

### AccessRoleRule (Правила доступа)

Правила доступа для ролей к бизнес-элементам.

```sql
CREATE TABLE authentication_accessrolerule (
    id UUID PRIMARY KEY,
    role_id UUID NOT NULL REFERENCES authentication_role(id) ON DELETE CASCADE,
    element_id UUID NOT NULL REFERENCES authentication_businesselement(id) ON DELETE CASCADE,
    read_permission BOOLEAN DEFAULT FALSE,
    read_all_permission BOOLEAN DEFAULT FALSE,
    create_permission BOOLEAN DEFAULT FALSE,
    update_permission BOOLEAN DEFAULT FALSE,
    update_all_permission BOOLEAN DEFAULT FALSE,
    delete_permission BOOLEAN DEFAULT FALSE,
    delete_all_permission BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_id, element_id)
);
```

**Поля прав доступа:**
- `read_permission` - Чтение своих объектов
- `read_all_permission` - Чтение всех объектов
- `create_permission` - Создание объектов
- `update_permission` - Обновление своих объектов
- `update_all_permission` - Обновление всех объектов
- `delete_permission` - Удаление своих объектов
- `delete_all_permission` - Удаление всех объектов

### Session (Сессии)

Управление JWT сессиями пользователей.

```sql
CREATE TABLE authentication_session (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES authentication_user(id) ON DELETE CASCADE,
    access_jti VARCHAR(255) NOT NULL,
    refresh_jti VARCHAR(255) NOT NULL,
    access_expires_at DATETIME NOT NULL,
    refresh_expires_at DATETIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Поля:**
- `access_jti` - JWT ID для access токена
- `refresh_jti` - JWT ID для refresh токена
- `access_expires_at` - Дата истечения access токена
- `refresh_expires_at` - Дата истечения refresh токена
- `is_active` - Активна ли сессия

## 🏪 Mock Business App

### Shop (Магазины)

Магазины в системе маркетплейса.

```sql
CREATE TABLE mock_business_shop (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(20),
    owner_id UUID NOT NULL REFERENCES authentication_user(id) ON DELETE CASCADE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Поля:**
- `id` - Уникальный идентификатор магазина
- `name` - Название магазина
- `address` - Адрес магазина
- `phone` - Телефон магазина
- `owner_id` - Владелец магазина

### Product (Товары)

Товары в магазинах.

```sql
CREATE TABLE mock_business_product (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    shop_id UUID NOT NULL REFERENCES mock_business_shop(id) ON DELETE CASCADE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Поля:**
- `id` - Уникальный идентификатор товара
- `name` - Название товара
- `description` - Описание товара
- `price` - Цена товара
- `shop_id` - ID магазина

### Order (Заказы)

Заказы пользователей.

```sql
CREATE TABLE mock_business_order (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES mock_business_product(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES authentication_user(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    total_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Поля:**
- `id` - Уникальный идентификатор заказа
- `product_id` - ID товара
- `user_id` - ID пользователя
- `quantity` - Количество товара
- `total_price` - Общая стоимость
- `status` - Статус заказа (pending, completed, cancelled)

## 🔗 Связи и зависимости

### Диаграмма связей

```
User (1) -----> (M) UserRole (M) <---- (1) Role
  |                                         |
  |                                         |
  +-----> (1) Session                        |
  |                                         |
  +-----> (1) Shop (1) -----> (M) Product   |
  |                    |                     |
  |                    |                     |
  +-----> (M) Order <----+                     |
                                              |
Role (1) -----> (M) AccessRoleRule (M) <---- (1) BusinessElement
```

### Каскадное удаление

- При удалении пользователя удаляются:
  - Все его роли (UserRole)
  - Все его сессии (Session)
  - Все его магазины (Shop)
  - Все его заказы (Order)
- При удалении магазина удаляются все его товары (Product)
- При удалении товара удаляются все связанные заказы (Order)
- При удалении роли удаляются все правила доступа (AccessRoleRule)

## 📊 Индексы

### Основные индексы

```sql
-- User
CREATE INDEX idx_user_email ON authentication_user(email);
CREATE INDEX idx_user_is_active ON authentication_user(is_active);
CREATE INDEX idx_user_ban_until ON authentication_user(ban_until);

-- Session
CREATE INDEX idx_session_user_id ON authentication_session(user_id);
CREATE INDEX idx_session_access_jti ON authentication_session(access_jti);
CREATE INDEX idx_session_refresh_jti ON authentication_session(refresh_jti);
CREATE INDEX idx_session_is_active ON authentication_session(is_active);

-- Shop
CREATE INDEX idx_shop_owner_id ON mock_business_shop(owner_id);

-- Product
CREATE INDEX idx_product_shop_id ON mock_business_product(shop_id);

-- Order
CREATE INDEX idx_order_user_id ON mock_business_order(user_id);
CREATE INDEX idx_order_product_id ON mock_business_order(product_id);
CREATE INDEX idx_order_status ON mock_business_order(status);
```

## 🔒 Безопасность данных

### Хеширование паролей

- Используется bcrypt для хеширования паролей
- Соль генерируется автоматически
- Длина хеша: 128 символов

### JWT токены

- Access токены: 15 минут
- Refresh токены: 7 дней
- Уникальные JTI для каждого токена
- Хранение в базе данных для отзыва

### Проверка прав доступа

- Права проверяются на уровне middleware
- Гранулярный контроль для каждого бизнес-элемента
- Разделение прав на свои/чужие объекты

## 📈 Оптимизация производительности

### Рекомендации

1. **Индексы** - созданы для часто используемых полей
2. **Запросы** - оптимизированы с использованием select_related и prefetch_related
3. **Кэширование** - можно добавить Redis для сессий
4. **Пагинация** - реализована для списковых эндпоинтов

### Мониторинг

- Размер базы данных: ~5-10MB для 1000 пользователей
- Среднее время запроса: <50ms
- Пиковая нагрузка: ~100 одновременных пользователей

## 🔄 Миграции

### Текущие миграции

```
authentication/
├── 0001_initial.py    # Создание всех моделей аутентификации

mock_business/
├── 0001_initial.py    # Создание моделей бизнес-логики
```

### Будущие изменения

- Добавление полей для профилей пользователей
- Расширение системы прав доступа
- Добавление логирования действий

---

**Схема актуальна для версии 1.0**
