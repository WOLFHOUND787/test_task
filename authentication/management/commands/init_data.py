from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import User, Role, UserRole, BusinessElement, AccessRoleRule
import uuid


class Command(BaseCommand):
    help = 'Initialize database with basic roles, business elements and access rules'

    def handle(self, *args, **options):
        # Создаем роли
        roles_data = [
            {'name': 'admin', 'description': 'Администратор системы с полными правами'},
            {'name': 'manager', 'description': 'Менеджер с расширенными правами'},
            {'name': 'user', 'description': 'Обычный пользователь с базовыми правами'},
            {'name': 'guest', 'description': 'Гость с минимальными правами доступа'},
        ]
        
        created_roles = {}
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            created_roles[role_data['name']] = role
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created role: {role.name}"))

        # Создаем бизнес-элементы
        elements_data = [
            {'name': 'users', 'description': 'Пользователи системы', 'has_owner_field': True},
            {'name': 'products', 'description': 'Товары и продукты', 'has_owner_field': True},
            {'name': 'orders', 'description': 'Заказы покупателей', 'has_owner_field': True},
            {'name': 'shops', 'description': 'Магазины и точки продаж', 'has_owner_field': True},
            {'name': 'reports', 'description': 'Отчеты и аналитика', 'has_owner_field': False},
            {'name': 'roles', 'description': 'Роли пользователей', 'has_owner_field': False},
            {'name': 'business_elements', 'description': 'Бизнес-элементы системы', 'has_owner_field': False},
            {'name': 'access_rules', 'description': 'Правила доступа', 'has_owner_field': False},
            {'name': 'user_roles', 'description': 'Назначение ролей пользователям', 'has_owner_field': False},
        ]
        
        created_elements = {}
        for element_data in elements_data:
            element, created = BusinessElement.objects.get_or_create(
                name=element_data['name'],
                defaults={
                    'description': element_data['description'],
                    'has_owner_field': element_data['has_owner_field']
                }
            )
            created_elements[element_data['name']] = element
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created business element: {element.name}"))

        # Создаем правила доступа для ролей
        
        # Администратор - все права на все ресурсы
        admin_role = created_roles['admin']
        for element in created_elements.values():
            rule, created = AccessRoleRule.objects.get_or_create(
                role=admin_role,
                element=element,
                defaults={
                    'read_permission': True,
                    'read_all_permission': True,
                    'create_permission': True,
                    'update_permission': True,
                    'update_all_permission': True,
                    'delete_permission': True,
                    'delete_all_permission': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created admin rule for: {element.name}"))

        # Менеджер - расширенные права
        manager_role = created_roles['manager']
        manager_permissions = {
            'users': {'read': True, 'read_all': True, 'create': True, 'update': True, 'update_all': False, 'delete': True, 'delete_all': False},
            'products': {'read': True, 'read_all': True, 'create': True, 'update': True, 'update_all': True, 'delete': True, 'delete_all': False},
            'orders': {'read': True, 'read_all': True, 'create': True, 'update': True, 'update_all': True, 'delete': True, 'delete_all': False},
            'shops': {'read': True, 'read_all': True, 'create': True, 'update': True, 'update_all': False, 'delete': True, 'delete_all': False},
            'reports': {'read': True, 'read_all': True, 'create': False, 'update': False, 'update_all': False, 'delete': False, 'delete_all': False},
        }
        
        for element_name, permissions in manager_permissions.items():
            if element_name in created_elements:
                element = created_elements[element_name]
                rule, created = AccessRoleRule.objects.get_or_create(
                    role=manager_role,
                    element=element,
                    defaults={
                        'read_permission': permissions['read'],
                        'read_all_permission': permissions['read_all'],
                        'create_permission': permissions['create'],
                        'update_permission': permissions['update'],
                        'update_all_permission': permissions['update_all'],
                        'delete_permission': permissions['delete'],
                        'delete_all_permission': permissions['delete_all'],
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created manager rule for: {element.name}"))

        # Пользователь - базовые права
        user_role = created_roles['user']
        user_permissions = {
            'users': {'read': True, 'read_all': False, 'create': False, 'update': True, 'update_all': False, 'delete': False, 'delete_all': False},
            'products': {'read': True, 'read_all': False, 'create': True, 'update': True, 'update_all': False, 'delete': True, 'delete_all': False},
            'orders': {'read': True, 'read_all': False, 'create': True, 'update': True, 'update_all': False, 'delete': True, 'delete_all': False},
            'shops': {'read': True, 'read_all': False, 'create': False, 'update': False, 'update_all': False, 'delete': False, 'delete_all': False},
        }
        
        for element_name, permissions in user_permissions.items():
            if element_name in created_elements:
                element = created_elements[element_name]
                rule, created = AccessRoleRule.objects.get_or_create(
                    role=user_role,
                    element=element,
                    defaults={
                        'read_permission': permissions['read'],
                        'read_all_permission': permissions['read_all'],
                        'create_permission': permissions['create'],
                        'update_permission': permissions['update'],
                        'update_all_permission': permissions['update_all'],
                        'delete_permission': permissions['delete'],
                        'delete_all_permission': permissions['delete_all'],
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created user rule for: {element.name}"))

        # Гость - минимальные права
        guest_role = created_roles['guest']
        guest_permissions = {
            'products': {'read': True, 'read_all': False, 'create': False, 'update': False, 'update_all': False, 'delete': False, 'delete_all': False},
            'shops': {'read': True, 'read_all': False, 'create': False, 'update': False, 'update_all': False, 'delete': False, 'delete_all': False},
        }
        
        for element_name, permissions in guest_permissions.items():
            if element_name in created_elements:
                element = created_elements[element_name]
                rule, created = AccessRoleRule.objects.get_or_create(
                    role=guest_role,
                    element=element,
                    defaults={
                        'read_permission': permissions['read'],
                        'read_all_permission': permissions['read_all'],
                        'create_permission': permissions['create'],
                        'update_permission': permissions['update'],
                        'update_all_permission': permissions['update_all'],
                        'delete_permission': permissions['delete'],
                        'delete_all_permission': permissions['delete_all'],
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created guest rule for: {element.name}"))

        # Создаем тестового администратора
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            UserRole.objects.create(user=admin_user, role=admin_role)
            self.stdout.write(self.style.SUCCESS("Created admin user: admin@example.com / admin123"))

        # Создаем тестового менеджера
        manager_user, created = User.objects.get_or_create(
            email='manager@example.com',
            defaults={
                'first_name': 'Manager',
                'last_name': 'User',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        if created:
            manager_user.set_password('manager123')
            manager_user.save()
            UserRole.objects.create(user=manager_user, role=manager_role)
            self.stdout.write(self.style.SUCCESS("Created manager user: manager@example.com / manager123"))

        # Создаем тестового обычного пользователя
        regular_user, created = User.objects.get_or_create(
            email='user@example.com',
            defaults={
                'first_name': 'Regular',
                'last_name': 'User',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        if created:
            regular_user.set_password('user123')
            regular_user.save()
            UserRole.objects.create(user=regular_user, role=user_role)
            self.stdout.write(self.style.SUCCESS("Created regular user: user@example.com / user123"))

        self.stdout.write(self.style.SUCCESS('Database initialization completed successfully!'))
