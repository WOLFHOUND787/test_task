from django.contrib import admin
from .models import User, Session, Role, UserRole, BusinessElement, AccessRoleRule


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'token_jti', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['user__email', 'token_jti']
    readonly_fields = ['id', 'created_at']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_at', 'assigned_by']
    list_filter = ['assigned_at', 'role']
    search_fields = ['user__email', 'role__name']
    readonly_fields = ['id', 'assigned_at']


@admin.register(BusinessElement)
class BusinessElementAdmin(admin.ModelAdmin):
    list_display = ['name', 'has_owner_field', 'is_active']
    list_filter = ['is_active', 'has_owner_field']
    search_fields = ['name', 'description']


@admin.register(AccessRoleRule)
class AccessRoleRuleAdmin(admin.ModelAdmin):
    list_display = ['role', 'element', 'read_permission', 'create_permission', 'update_permission', 'delete_permission']
    list_filter = ['role', 'element', 'read_permission', 'create_permission', 'update_permission', 'delete_permission']
    search_fields = ['role__name', 'element__name']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('role', 'element')
        }),
        ('Read Permissions', {
            'fields': ('read_permission', 'read_all_permission')
        }),
        ('Create Permissions', {
            'fields': ('create_permission',)
        }),
        ('Update Permissions', {
            'fields': ('update_permission', 'update_all_permission')
        }),
        ('Delete Permissions', {
            'fields': ('delete_permission', 'delete_all_permission')
        }),
    )
