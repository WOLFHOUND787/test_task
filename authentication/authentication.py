from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.deprecation import MiddlewareMixin
from .models import User, Session
from .utils import verify_jwt_token
from django.conf import settings


class JWTAuthentication(BaseAuthentication):
    """
    Кастомная аутентификация через JWT токен
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        
        if not payload:
            raise AuthenticationFailed('Invalid or expired token')
            
        try:
            session = Session.objects.get(token_jti=payload['jti'], is_active=True)
            if not session.is_active or session.expires_at < timezone.now():
                raise AuthenticationFailed('Session expired')
                
            user = session.user
            if not user.is_active:
                raise AuthenticationFailed('User account is disabled')
                
            return (user, token)
        except (Session.DoesNotExist, User.DoesNotExist):
            raise AuthenticationFailed('Invalid token')


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware для автоматической аутентификации пользователя
    """
    
    def process_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            
            if payload:
                try:
                    session = Session.objects.get(token_jti=payload['jti'], is_active=True)
                    if session.is_active and session.expires_at >= timezone.now():
                        user = session.user
                        if user.is_active:
                            request.user = user
                            request.session_obj = session
                except (Session.DoesNotExist, User.DoesNotExist):
                    pass
        
        return None


from django.utils import timezone
