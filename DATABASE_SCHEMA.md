# Схема базы данных для системы аутентификации и авторизации

## Обзор

Система основана на ролевой модели доступа с гибкими правилами разграничения прав доступа.

## Таблицы аутентификации

### users
Пользовательская модель с расширенными полями
- **id** (PK) - Уникальный идентификатор
- **email** (EmailField, unique) - Email пользователя (используется для логина)
- **first_name** (CharField) - Имя
- **last_name** (CharField) - Фамилия
- **patronymic** (CharField, optional) - Отчество
- **password_hash** (CharField) - Хеш пароля (bcrypt)
- **is_active** (BooleanField) - Активность аккаунта (мягкое удаление)
- **is_staff** (BooleanField) - Доступ к админке
- **is_superuser** (BooleanField) - Суперпользователь
- **created_at** (DateTimeField) - Дата создания
- **updated_at** (DateTimeField) - Дата обновления

### sessions
Сессии пользователей для JWT токенов
- **id** (PK) - Уникальный идентификатор
- **user_id** (FK -> users.id) - ID пользователя
- **token_jti** (CharField, unique) - JWT Token ID
- **expires_at** (DateTimeField) - Время истечения токена
- **created_at** (DateTimeField) - Дата создания
- **is_active** (BooleanField) - Активность сессии

## Таблицы авторизации

### roles
Роли пользователей в системе
- **id** (PK) - Уникальный идентификатор
- **name** (CharField, unique) - Название роли (admin, manager, user, guest)
- **description** (TextField) - Описание роли
- **is_active** (BooleanField) - Активность роли

### user_roles
Связь пользователей с ролями (многие ко многим)
- **id** (PK) - Уникальный идентификатор
- **user_id** (FK -> users.id) - ID пользователя
- **role_id** (FK -> roles.id) - ID роли
- **assigned_at** (DateTimeField) - Дата назначения роли
- **assigned_by** (FK -> users.id) - Кто назначил роль

### business_elements
Объекты бизнес-логики, к которым ограничивается доступ
- **id** (PK) - Уникальный идентификатор
- **name** (CharField, unique) - Название элемента (users, products, orders, etc.)
- **description** (TextField) - Описание элемента
- **has_owner_field** (BooleanField) - Есть ли у элемента поле owner
- **is_active** (BooleanField) - Активность элемента

### access_roles_rules
Правила доступа для ролей к бизнес-элементам
- **id** (PK) - Уникальный идентификатор
- **role_id** (FK -> roles.id) - ID роли
- **element_id** (FK -> business_elements.id) - ID бизнес-элемента
- **read_permission** (BooleanField) - Право на чтение своих объектов
- **read_all_permission** (BooleanField) - Право на чтение всех объектов
- **create_permission** (BooleanField) - Право на создание
- **update_permission** (BooleanField) - Право на обновление своих объектов
- **update_all_permission** (BooleanField) - Право на обновление всех объектов
- **delete_permission** (BooleanField) - Право на удаление своих объектов
- **delete_all_permission** (BooleanField) - Право на удаление всех объектов

## Логика проверки прав доступа

1. **Определение пользователя**: Из JWT токена через middleware
2. **Проверка аутентификации**: Если токен отсутствует или невалиден -> 401
3. **Определение ресурса**: Из URL и HTTP метода
4. **Проверка прав**: 
   - Найти все роли пользователя
   - Найти правила доступа для этих ролей к запрашиваемому ресурсу
   - Проверить соответствие права (read/create/update/delete)
   - Если ресурс имеет владельца, проверить является ли пользователь владельцем
5. **Результат**: Есть права -> доступ разрешен, нет прав -> 403

## Примеры правил

### Администратор (admin)
- Все права на все ресурсы (all_permission = true)

### Менеджер (manager)
- Чтение всех пользователей, заказов, товаров
- Создание заказов, товаров
- Обновление заказов, товаров
- Удаление только созданных им объектов

### Пользователь (user)
- Чтение и обновление только своего профиля
- Чтение своих заказов
- Создание заказов

### Гость (guest)
- Только чтение публичных данных (товары, каталоги)
