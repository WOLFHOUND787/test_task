from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
import bcrypt
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, patronymic=None, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
        )
        
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, first_name, last_name, password):
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name='Email')
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    patronymic = models.CharField(max_length=50, blank=True, null=True, verbose_name='Отчество')
    password_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_staff = models.BooleanField(default=False, verbose_name='Персонал')
    is_superuser = models.BooleanField(default=False, verbose_name='Суперпользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def set_password(self, raw_password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(raw_password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password_hash.encode('utf-8'))

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions', verbose_name='Пользователь')
    access_jti = models.CharField(max_length=255, unique=True, verbose_name='Access JTI')
    refresh_jti = models.CharField(max_length=255, unique=True, verbose_name='Refresh JTI')
    access_expires_at = models.DateTimeField(verbose_name='Истекает access токен')
    refresh_expires_at = models.DateTimeField(default=timezone.now() + timedelta(days=7), verbose_name='Истекает refresh токен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        db_table = 'sessions'
        verbose_name = 'Сессия'
        verbose_name_plural = 'Сессии'


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        db_table = 'roles'
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self):
        return self.name


class UserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles', verbose_name='Пользователь')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users', verbose_name='Роль')
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='Назначена')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_roles', verbose_name='Кем назначена')

    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'


class BusinessElement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    has_owner_field = models.BooleanField(default=False, verbose_name='Есть поле владельца')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'business_elements'
        verbose_name = 'Бизнес-элемент'
        verbose_name_plural = 'Бизнес-элементы'

    def __str__(self):
        return self.name


class AccessRoleRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='access_rules', verbose_name='Роль')
    element = models.ForeignKey(BusinessElement, on_delete=models.CASCADE, related_name='access_rules', verbose_name='Элемент')
    read_permission = models.BooleanField(default=False, verbose_name='Чтение')
    read_all_permission = models.BooleanField(default=False, verbose_name='Чтение всех')
    create_permission = models.BooleanField(default=False, verbose_name='Создание')
    update_permission = models.BooleanField(default=False, verbose_name='Обновление')
    update_all_permission = models.BooleanField(default=False, verbose_name='Обновление всех')
    delete_permission = models.BooleanField(default=False, verbose_name='Удаление')
    delete_all_permission = models.BooleanField(default=False, verbose_name='Удаление всех')

    class Meta:
        db_table = 'access_roles_rules'
        verbose_name = 'Правило доступа'
        verbose_name_plural = 'Правила доступа'
        unique_together = ['role', 'element']

    def __str__(self):
        return f"{self.role.name} - {self.element.name}"
