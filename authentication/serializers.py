from rest_framework import serializers
from .models import User, Role, UserRole, BusinessElement, AccessRoleRule
from django.utils import timezone


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['user', 'manager'], default='user')
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'password_confirm', 'role']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        role_name = validated_data.pop('role', 'user')
        
        user = User.objects.create_user(**validated_data)
        
        # Назначаем выбранную роль
        try:
            role = Role.objects.get(name=role_name)
            UserRole.objects.create(user=user, role=role)
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
            user = User.objects.get(email=email, is_active=True)
            if not user.check_password(password):
                raise serializers.ValidationError("Invalid credentials")
            attrs['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")
        
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
