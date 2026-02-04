from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from .models import User, Session, Role, UserRole, BusinessElement, AccessRoleRule
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserUpdateSerializer, RoleSerializer, BusinessElementSerializer,
    AccessRoleRuleSerializer, UserRoleSerializer
)
from .utils import generate_jwt_tokens, verify_refresh_token
from .authorization import check_user_permission, CustomObjectPermission


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Назначаем роль "user" по умолчанию
        try:
            user_role = Role.objects.get(name='user')
            UserRole.objects.create(user=user, role=user_role)
        except Role.DoesNotExist:
            pass
        
        return Response(
            {'message': 'User registered successfully'},
            status=status.HTTP_201_CREATED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Вход пользователя в систему"""
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    
    # Генерируем access и refresh токены
    access_token, refresh_token, access_jti, refresh_jti = generate_jwt_tokens(user.id)
    
    # Создаем сессию
    access_expires_at = timezone.now() + timedelta(minutes=15)
    refresh_expires_at = timezone.now() + timedelta(days=7)
    session = Session.objects.create(
        user=user,
        access_jti=access_jti,
        refresh_jti=refresh_jti,
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at
    )
    
    return Response({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'access_expires_at': access_expires_at,
        'refresh_expires_at': refresh_expires_at,
        'user': UserProfileSerializer(user).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Выход пользователя из системы"""
    try:
        if hasattr(request, 'session_obj'):
            request.session_obj.is_active = False
            request.session_obj.save()
        else:
            # Деактивируем все сессии пользователя
            Session.objects.filter(user=request.user, is_active=True).update(is_active=False)
        
        return Response({'message': 'Logged out successfully'})
    except Exception as e:
        return Response(
            {'error': 'Logout failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """Обновление access токена через refresh токен"""
    refresh_token = request.data.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем refresh токен
    payload = verify_refresh_token(refresh_token)
    if not payload:
        return Response(
            {'error': 'Invalid or expired refresh token'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Находим сессию по refresh_jti
        session = Session.objects.get(refresh_jti=payload['jti'], is_active=True)
        
        # Проверяем, что refresh токен еще не истек
        if session.refresh_expires_at < timezone.now():
            session.is_active = False
            session.save()
            return Response(
                {'error': 'Refresh token expired'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Генерируем новую пару токенов
        new_access_token, new_refresh_token, new_access_jti, new_refresh_jti = generate_jwt_tokens(session.user.id)
        
        # Обновляем сессию
        session.access_jti = new_access_jti
        session.refresh_jti = new_refresh_jti
        session.access_expires_at = timezone.now() + timedelta(minutes=15)
        session.refresh_expires_at = timezone.now() + timedelta(days=7)
        session.save()
        
        return Response({
            'access_token': new_access_token,
            'refresh_token': new_refresh_token,
            'access_expires_at': session.access_expires_at,
            'refresh_expires_at': session.refresh_expires_at,
        })
        
    except Session.DoesNotExist:
        return Response(
            {'error': 'Invalid session'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Просмотр и обновление профиля пользователя"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserProfileSerializer


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account_view(request):
    """Мягкое удаление аккаунта пользователя"""
    user = request.user
    user.is_active = False
    user.save()
    
    # Деактивируем все сессии
    Session.objects.filter(user=user, is_active=True).update(is_active=False)
    
    return Response({'message': 'Account deleted successfully'})


# Admin API для управления ролями и правами доступа

class RoleListCreateView(generics.ListCreateAPIView):
    """Список и создание ролей"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, CustomObjectPermission('roles', 'read')]
    
    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, CustomObjectPermission('roles', 'create')]
        return super().get_permissions()


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр, обновление и удаление роли"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, CustomObjectPermission('roles', 'read')]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            self.permission_classes = [IsAuthenticated, CustomObjectPermission('roles', 'update')]
        elif self.request.method == 'DELETE':
            self.permission_classes = [IsAuthenticated, CustomObjectPermission('roles', 'delete')]
        return super().get_permissions()


class BusinessElementListCreateView(generics.ListCreateAPIView):
    """Список и создание бизнес-элементов"""
    queryset = BusinessElement.objects.all()
    serializer_class = BusinessElementSerializer
    permission_classes = [IsAuthenticated, CustomObjectPermission('business_elements', 'read')]
    
    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, CustomObjectPermission('business_elements', 'create')]
        return super().get_permissions()


class AccessRoleRuleListCreateView(generics.ListCreateAPIView):
    """Список и создание правил доступа"""
    queryset = AccessRoleRule.objects.select_related('role', 'element').all()
    serializer_class = AccessRoleRuleSerializer
    permission_classes = [IsAuthenticated, CustomObjectPermission('access_rules', 'read')]
    
    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, CustomObjectPermission('access_rules', 'create')]
        return super().get_permissions()


class AccessRoleRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр, обновление и удаление правил доступа"""
    queryset = AccessRoleRule.objects.select_related('role', 'element').all()
    serializer_class = AccessRoleRuleSerializer
    permission_classes = [IsAuthenticated, CustomObjectPermission('access_rules', 'read')]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            self.permission_classes = [IsAuthenticated, CustomObjectPermission('access_rules', 'update')]
        elif self.request.method == 'DELETE':
            self.permission_classes = [IsAuthenticated, CustomObjectPermission('access_rules', 'delete')]
        return super().get_permissions()


class UserRoleListCreateView(generics.ListCreateAPIView):
    """Список и назначение ролей пользователям"""
    queryset = UserRole.objects.select_related('user', 'role').all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, CustomObjectPermission('user_roles', 'read')]
    
    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, CustomObjectPermission('user_roles', 'create')]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)


class UserRoleDetailView(generics.RetrieveDestroyAPIView):
    """Просмотр и удаление ролей пользователей"""
    queryset = UserRole.objects.select_related('user', 'role').all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, CustomObjectPermission('user_roles', 'read')]
    
    def get_permissions(self):
        if self.request.method == 'DELETE':
            self.permission_classes = [IsAuthenticated, CustomObjectPermission('user_roles', 'delete')]
        return super().get_permissions()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_permissions_view(request):
    """Просмотр прав доступа текущего пользователя"""
    user = request.user
    
    # Получаем все роли пользователя
    user_roles = user.user_roles.select_related('role').all()
    role_ids = [ur.role.id for ur in user_roles]
    
    # Получаем все правила доступа для ролей пользователя
    rules = AccessRoleRule.objects.select_related('role', 'element').filter(
        role_id__in=role_ids,
        role__is_active=True,
        element__is_active=True
    )
    
    permissions = {}
    for rule in rules:
        element_name = rule.element.name
        if element_name not in permissions:
            permissions[element_name] = {
                'read': False,
                'read_all': False,
                'create': False,
                'update': False,
                'update_all': False,
                'delete': False,
                'delete_all': False,
            }
        
        permissions[element_name]['read'] = permissions[element_name]['read'] or rule.read_permission
        permissions[element_name]['read_all'] = permissions[element_name]['read_all'] or rule.read_all_permission
        permissions[element_name]['create'] = permissions[element_name]['create'] or rule.create_permission
        permissions[element_name]['update'] = permissions[element_name]['update'] or rule.update_permission
        permissions[element_name]['update_all'] = permissions[element_name]['update_all'] or rule.update_all_permission
        permissions[element_name]['delete'] = permissions[element_name]['delete'] or rule.delete_permission
        permissions[element_name]['delete_all'] = permissions[element_name]['delete_all'] or rule.delete_all_permission
    
    return Response({
        'user_id': str(user.id),
        'email': user.email,
        'roles': [{'id': str(ur.role.id), 'name': ur.role.name} for ur in user_roles],
        'permissions': permissions
    })
