import jwt
from django.conf import settings
from datetime import datetime, timedelta
import uuid


def generate_jwt_tokens(user_id):
    """
    Генерирует access и refresh JWT токены для пользователя
    """
    access_jti = str(uuid.uuid4())
    refresh_jti = str(uuid.uuid4())
    
    # Access токен - короткоживущий (15 минут)
    access_payload = {
        'user_id': str(user_id),
        'jti': access_jti,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'iat': datetime.utcnow(),
    }
    
    # Refresh токен - долгоживущий (7 дней)
    refresh_payload = {
        'user_id': str(user_id),
        'jti': refresh_jti,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow(),
    }
    
    access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return access_token, refresh_token, access_jti, refresh_jti


def verify_jwt_token(token):
    """
    Проверяет JWT токен и возвращает payload
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token):
    """
    Проверяет refresh токен и возвращает payload
    """
    payload = verify_jwt_token(token)
    if payload and payload.get('type') == 'refresh':
        return payload
    return None
