from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User, Session, Role, UserRole, BusinessElement, AccessRoleRule


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('email', 'first_name', 'last_name', 'patronymic')
        }),
        ('Статус', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Системная информация', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Полное имя'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('user_roles__role')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'created_at', 'access_expires_at', 'session_actions']
    list_filter = ['is_active', 'created_at']
    search_fields = ('user__email',)
    readonly_fields = ['id', 'access_jti', 'refresh_jti', 'created_at']
    
    fieldsets = (
        ('Информация о сессии', {
            'fields': ('user', 'is_active')
        }),
        ('Токены', {
            'fields': ('access_jti', 'refresh_jti'),
            'classes': ('collapse',)
        }),
        ('Срок действия', {
            'fields': ('access_expires_at', 'refresh_expires_at')
        }),
        ('Системная информация', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def session_actions(self, obj):
        if obj.is_active:
            return format_html(
                '<button onclick="if(confirm(\'Деактивировать сессию?\')) {{ window.location.href=\'/admin/deactivate_session/{}/\'; }}">Деактивировать</button>',
                obj.id
            )
        return format_html('<span style="color: #999;">Неактивна</span>')
    session_actions.short_description = 'Действия'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'users_count']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'is_active')
        }),
    )
    
    def users_count(self, obj):
        return obj.role_users.count()
    users_count.short_description = 'Кол-во пользователей'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('role_users')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_at', 'assigned_by']
    list_filter = ['assigned_at', 'role']
    search_fields = ['user__email', 'role__name']
    readonly_fields = ['id', 'assigned_at']
    
    fieldsets = (
        ('Назначение роли', {
            'fields': ('user', 'role', 'assigned_by')
        }),
        ('Системная информация', {
            'fields': ('id', 'assigned_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'role', 'assigned_by')


@admin.register(BusinessElement)
class BusinessElementAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'has_owner_field', 'is_active', 'rules_count']
    list_filter = ['is_active', 'has_owner_field']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'has_owner_field', 'is_active')
        }),
    )
    
    def rules_count(self, obj):
        return obj.access_rules.count()
    rules_count.short_description = 'Кол-во правил'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('access_rules')


@admin.register(AccessRoleRule)
class AccessRoleRuleAdmin(admin.ModelAdmin):
    list_display = ['role', 'element', 'get_permissions_summary', 'permission_count']
    list_filter = ['role', 'element']
    search_fields = ['role__name', 'element__name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('role', 'element')
        }),
        ('Права на чтение', {
            'fields': ('read_permission', 'read_all_permission')
        }),
        ('Права на создание', {
            'fields': ('create_permission',)
        }),
        ('Права на обновление', {
            'fields': ('update_permission', 'update_all_permission')
        }),
        ('Права на удаление', {
            'fields': ('delete_permission', 'delete_all_permission')
        }),
    )
    
    def get_permissions_summary(self, obj):
        permissions = []
        if obj.read_permission:
            permissions.append('чтение')
        if obj.read_all_permission:
            permissions.append('чтение всех')
        if obj.create_permission:
            permissions.append('создание')
        if obj.update_permission:
            permissions.append('обновление')
        if obj.update_all_permission:
            permissions.append('обновление всех')
        if obj.delete_permission:
            permissions.append('удаление')
        if obj.delete_all_permission:
            permissions.append('удаление всех')
        return ', '.join(permissions) if permissions else 'нет прав'
    
    def permission_count(self, obj):
        count = sum([
            obj.read_permission, obj.read_all_permission, obj.create_permission,
            obj.update_permission, obj.update_all_permission,
            obj.delete_permission, obj.delete_all_permission
        ])
        return count
    permission_count.short_description = 'Кол-во прав'


# Русифицированные заголовки админки
admin.site.site_header = '🛍️ Панель управления маркетплейсом'
admin.site.site_title = 'Администрирование'
admin.site.index_title = 'Добро пожаловать в панель управления'
