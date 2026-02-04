from rest_framework.permissions import BasePermission
from django.http import HttpResponseForbidden
from functools import wraps
from .models import AccessRoleRule, BusinessElement


class AuthorizationError(Exception):
    pass


def check_user_permission(user, resource_name, action, obj_owner_id=None):
    """
    Проверяет права пользователя на выполнение действия с ресурсом
    
    Args:
        user: Объект пользователя
        resource_name: Название ресурса (например, 'users', 'products')
        action: Действие ('read', 'create', 'update', 'delete')
        obj_owner_id: ID владельца объекта (для проверки своих/чужих объектов)
    
    Returns:
        bool: True если разрешено, False если запрещено
    """
    if user.is_superuser:
        return True
    
    # Получаем все роли пользователя
    user_roles = user.user_roles.select_related('role').all()
    role_ids = [ur.role.id for ur in user_roles]
    
    # Получаем бизнес-элемент
    try:
        element = BusinessElement.objects.get(name=resource_name, is_active=True)
    except BusinessElement.DoesNotExist:
        return False
    
    # Получаем правила доступа для ролей пользователя
    rules = AccessRoleRule.objects.filter(
        role_id__in=role_ids,
        element=element,
        role__is_active=True
    )
    
    # Проверяем права
    has_permission = False
    has_all_permission = False
    
    for rule in rules:
        if action == 'read':
            if rule.read_all_permission:
                has_all_permission = True
                break
            elif rule.read_permission:
                has_permission = True
        elif action == 'create':
            if rule.create_permission:
                has_permission = True
                break
        elif action == 'update':
            if rule.update_all_permission:
                has_all_permission = True
                break
            elif rule.update_permission:
                has_permission = True
        elif action == 'delete':
            if rule.delete_all_permission:
                has_all_permission = True
                break
            elif rule.delete_permission:
                has_permission = True
    
    # Если есть права на все объекты
    if has_all_permission:
        return True
    
    # Если есть права только на свои объекты
    if has_permission:
        # Для действий create не нужен владелец
        if action == 'create':
            return True
        
        # Для чтения списка (read) разрешаем доступ, фильтрация будет на уровне view
        if action == 'read':
            return True
        
        # Для других действий проверяем владельца
        if obj_owner_id is not None and str(obj_owner_id) == str(user.id):
            return True
    
    return False


class CustomObjectPermission(BasePermission):
    """
    Кастомный permission класс для DRF
    """
    
    def __init__(self, resource_name, action='read'):
        self.resource_name = resource_name
        self.action = action
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Для create не нужен конкретный объект
        if self.action == 'create':
            return check_user_permission(request.user, self.resource_name, 'create')
        
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Определяем владельца объекта
        obj_owner_id = None
        if hasattr(obj, 'owner'):
            obj_owner_id = obj.owner.id if obj.owner else None
        elif hasattr(obj, 'user'):
            obj_owner_id = obj.user.id if obj.user else None
        elif hasattr(obj, 'id') and self.resource_name == 'users':
            obj_owner_id = obj.id
        
        return check_user_permission(
            request.user, 
            self.resource_name, 
            self.action, 
            obj_owner_id
        )


def CustomObjectPermissionFactory(resource_name, action='read'):
    """
    Фабрика для создания permission классов
    """
    class PermissionClass(BasePermission):
        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            
            # Для create не нужен конкретный объект
            if action == 'create':
                return check_user_permission(request.user, resource_name, 'create')
            
            return True
        
        def has_object_permission(self, request, view, obj):
            if not request.user or not request.user.is_authenticated:
                return False
            
            # Определяем владельца объекта
            obj_owner_id = None
            if hasattr(obj, 'owner'):
                obj_owner_id = obj.owner.id if obj.owner else None
            elif hasattr(obj, 'user'):
                obj_owner_id = obj.user.id if obj.user else None
            elif hasattr(obj, 'id') and resource_name == 'users':
                obj_owner_id = obj.id
            
            return check_user_permission(
                request.user, 
                resource_name, 
                action, 
                obj_owner_id
            )
    
    return PermissionClass


def require_permission(resource_name, action='read'):
    """
    Декоратор для проверки прав доступа во view функциях
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return HttpResponseForbidden({"error": "Authentication required"})
            
            # Для объектов получаем ID из kwargs
            obj_owner_id = None
            if action in ['update', 'delete'] and 'pk' in kwargs:
                # Здесь должна быть логика получения владельца объекта
                # Для простоты пока пропустим
                pass
            
            if not check_user_permission(request.user, resource_name, action, obj_owner_id):
                return HttpResponseForbidden({"error": "Insufficient permissions"})
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
