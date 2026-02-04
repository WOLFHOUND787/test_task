import jwt
from django.conf import settings
from datetime import datetime, timedelta
import uuid


def generate_jwt_token(user_id):
    """
    Генерирует JWT токен для пользователя
    """
    jti = str(uuid.uuid4())
    payload = {
        'user_id': str(user_id),
        'jti': jti,
        'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME),
        'iat': datetime.utcnow(),
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


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
