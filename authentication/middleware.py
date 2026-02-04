from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden, JsonResponse
from .utils import verify_jwt_token
from .models import User, Session
from django.utils import timezone


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware для автоматической аутентификации пользователя
    """
    
    def process_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            
            if payload and payload.get('type') == 'access':
                try:
                    session = Session.objects.get(access_jti=payload['jti'], is_active=True)
                    if session.is_active and session.access_expires_at >= timezone.now():
                        user = session.user
                        if user.is_active:
                            request.user = user
                            request.session_obj = session
                except (Session.DoesNotExist, User.DoesNotExist):
                    pass
        
        return None


class AuthorizationMiddleware(MiddlewareMixin):
    """
    Middleware для проверки прав доступа на основе URL и HTTP метода
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Пропускаем аутентификационные эндпоинты
        if request.path in ['/api/auth/register/', '/api/auth/login/']:
            return None
        
        # Если пользователь не аутентифицирован, возвращаем 401
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Определяем ресурс и действие из URL и метода
        resource_name, action = self._parse_request(request)
        
        if resource_name and action:
            from .authorization import check_user_permission
            
            # Проверяем права доступа
            if not check_user_permission(request.user, resource_name, action):
                return JsonResponse({'error': 'Insufficient permissions'}, status=403)
        
        return None
    
    def _parse_request(self, request):
        """
        Определяет ресурс и действие из запроса
        """
        path = request.path
        method = request.method
        
        # Карта путей к ресурсам
        path_mapping = {
            '/api/auth/profile/': ('users', 'read'),
            '/api/auth/permissions/': ('permissions', 'read'),
            '/api/admin/roles/': ('roles', 'read'),
            '/api/admin/business-elements/': ('business_elements', 'read'),
            '/api/admin/access-rules/': ('access_rules', 'read'),
            '/api/admin/user-roles/': ('user_roles', 'read'),
        }
        
        # Определяем действие по HTTP методу
        action_mapping = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        
        action = action_mapping.get(method, 'read')
        
        # Ищем точное совпадение пути
        for path_pattern, (resource, default_action) in path_mapping.items():
            if path.startswith(path_pattern):
                if method == 'GET' and path == path_pattern:
                    return resource, default_action
                elif method == 'POST' and path == path_pattern:
                    return resource, 'create'
                elif method in ['PUT', 'PATCH', 'DELETE'] and '<uuid:pk>' in path:
                    return resource, action
        
        # Для детальных эндпоинтов
        for path_pattern, (resource, _) in path_mapping.items():
            if path.startswith(path_pattern) and '<uuid:pk>' in path_pattern:
                return resource, action
        
        return None, None
