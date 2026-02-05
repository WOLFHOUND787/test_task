from rest_framework import serializers
from .models import User, Role, UserRole, BusinessElement, AccessRoleRule
from django.utils import timezone


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['user', 'manager'], default='user')
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm', 'role']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        role_name = validated_data.pop('role', 'user')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        
        # Назначаем выбранную роль
        try:
            role = Role.objects.get(name=role_name)
            # Проверяем что у пользователя еще нет такой роли
            if not UserRole.objects.filter(user=user, role=role).exists():
                UserRole.objects.create(user=user, role=role)
                
                # Создаем базовые права для новой роли
                from authentication.models import BusinessElement, AccessRoleRule
                
                # Создаем базовые элементы если их нет
                basic_elements = ['shops', 'products', 'orders', 'users']
                for element_name in basic_elements:
                    BusinessElement.objects.get_or_create(
                        name=element_name,
                        defaults={
                            'description': f'Бизнес-элемент {element_name}',
                            'has_owner_field': True,
                            'is_active': True
                        }
                    )
                
                if role_name == 'user':
                    # Даем права пользователя на чтение магазинов, продуктов, заказов
                    elements_data = [
                        ('shops', True, False, False, False, False),  # read
                        ('products', True, False, False, False, False),  # read
                        ('orders', True, False, False, False, False),  # read
                    ]
                elif role_name == 'manager':
                    # Даем полные права менеджера
                    elements_data = [
                        ('shops', True, True, True, True, True),  # все права
                        ('products', True, True, True, True, True),  # все права
                        ('orders', True, True, True, True, True),  # все права
                    ]
                elif role_name == 'admin':
                    # Даем полные права админа + управление пользователями
                    elements_data = [
                        ('shops', True, True, True, True, True),  # все права
                        ('products', True, True, True, True, True),  # все права
                        ('orders', True, True, True, True, True),  # все права
                        ('users', True, True, True, True, True),  # все права
                    ]
                else:
                    elements_data = []
                
                for element_data in elements_data:
                    element_name, read_perm, read_all, create_perm, update_all, delete_all = element_data
                    try:
                        element = BusinessElement.objects.get(name=element_name, is_active=True)
                        AccessRoleRule.objects.get_or_create(
                            role=role,
                            element=element,
                            defaults={
                                'read_permission': read_perm,
                                'read_all_permission': read_all,
                                'create_permission': create_perm,
                                'update_permission': update_all,
                                'update_all_permission': update_all,
                                'delete_permission': delete_all,
                                'delete_all_permission': delete_all,
                            }
                        )
                    except BusinessElement.DoesNotExist:
                        # Если элемента нет, создаем его
                        element = BusinessElement.objects.create(
                            name=element_name,
                            description=f'Элемент {element_name}',
                            has_owner_field=True,
                            is_active=True
                        )
                        AccessRoleRule.objects.create(
                            role=role,
                            element=element,
                            read_permission=read_perm,
                            read_all_permission=read_all,
                            create_permission=create_perm,
                            update_permission=update_all,
                            update_all_permission=update_all,
                            delete_permission=delete_all,
                            delete_all_permission=delete_all,
                        )
                        
        except Role.DoesNotExist:
            pass
        
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        try:
            # Ищем пользователя независимо от is_active статуса
            user = User.objects.get(email=email)
            
            # Проверяем пароль
            if not user.check_password(password):
                raise serializers.ValidationError("Неверный логин или пароль")
            
            # Проверяем не забанен ли пользователь
            if user.is_banned:
                ban_message = "Ваш аккаунт забанен"
                if user.ban_until:
                    ban_message += f" до {user.ban_until.strftime('%d.%m.%Y %H:%M')}"
                else:
                    ban_message += " навсегда"
                raise serializers.ValidationError(ban_message)
            
            attrs['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError("Неверный логин или пароль")
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'patronymic', 'full_name', 'is_active', 'created_at', 'roles']
        read_only_fields = ['id', 'is_active', 'created_at']
    
    def get_roles(self, obj):
        roles = obj.user_roles.select_related('role').all()
        return [{'id': str(role.role.id), 'name': role.role.name} for role in roles]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'patronymic']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'is_active']


class BusinessElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessElement
        fields = ['id', 'name', 'description', 'has_owner_field', 'is_active']


class AccessRoleRuleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    element_name = serializers.CharField(source='element.name', read_only=True)
    
    class Meta:
        model = AccessRoleRule
        fields = [
            'id', 'role', 'element', 'role_name', 'element_name',
            'read_permission', 'read_all_permission',
            'create_permission',
            'update_permission', 'update_all_permission',
            'delete_permission', 'delete_all_permission'
        ]


class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'role_name', 'user_email', 'assigned_at', 'assigned_by']
