"""
URL configuration for test_task project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/business/', include('mock_business.urls')),
]

# Обслуживание статических файлов в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Обслуживание фронтенда
def frontend_view(request):
    # Проверяем авторизацию и показываем нужную страницу
    token = request.COOKIES.get('accessToken') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if token:
        # Если есть токен, показываем маркетплейс
        try:
            from authentication.models import Session
            from django.utils import timezone
            import jwt
            from django.conf import settings
            
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            session = Session.objects.get(access_jti=payload['jti'], is_active=True)
            
            if session.is_active and session.access_expires_at >= timezone.now():
                return HttpResponse(open('templates/marketplace.html').read(), content_type='text/html')
        except:
            pass
    
    # Если нет токена или он недействителен, показываем страницу входа
    return HttpResponse(open('templates/marketplace.html').read(), content_type='text/html')

urlpatterns += [
    path('', frontend_view),
]
