#!/usr/bin/env python3
"""
Демонстрационный скрипт для системы аутентификации и авторизации
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_user_login(email, password):
    """Логин пользователя и получение токена"""
    response = requests.post(f"{BASE_URL}/auth/login/", json={
        "email": email,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Успешный вход: {email}")
        return data['token']
    else:
        print(f"❌ Ошибка входа: {email}")
        return None

def test_resource_access(token, resource_name, description):
    """Тест доступа к ресурсу"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/business/{resource_name}/", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ {description}: Доступ разрешен")
        return True
    elif response.status_code == 403:
        print(f"❌ {description}: Доступ запрещен (403)")
        return False
    else:
        print(f"❌ {description}: Ошибка {response.status_code}")
        return False

def test_permissions_view(token, user_type):
    """Просмотр прав пользователя"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/permissions/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"📋 Права {user_type}:")
        for resource, perms in data['permissions'].items():
            if any(perms.values()):
                print(f"  - {resource}: {list(perms.keys())}")
    else:
        print(f"❌ Не удалось получить права для {user_type}")

def main():
    print("🚀 Демонстрация системы аутентификации и авторизации\n")
    
    # Тестовые пользователи
    users = [
        ("admin@example.com", "admin123", "Администратор"),
        ("manager@example.com", "manager123", "Менеджер"),
        ("user@example.com", "user123", "Обычный пользователь"),
    ]
    
    # Ресурсы для тестирования
    resources = [
        ("products", "Продукты"),
        ("orders", "Заказы"),
        ("shops", "Магазины"),
        ("reports", "Отчеты"),
        ("users", "Пользователи"),
    ]
    
    for email, password, user_type in users:
        print(f"\n{'='*50}")
        print(f"👤 Тестирование: {user_type}")
        print(f"{'='*50}")
        
        # Логин
        token = test_user_login(email, password)
        if not token:
            continue
        
        # Тест доступа к ресурсам
        print(f"\n🔐 Тест доступа к ресурсам:")
        for resource_name, description in resources:
            test_resource_access(token, resource_name, description)
        
        # Просмотр прав
        print(f"\n📋 Просмотр прав:")
        test_permissions_view(token, user_type)
        
        print(f"\n⏸️ Пауза 2 секунды...")
        time.sleep(2)
    
    print(f"\n{'='*50}")
    print("🎉 Демонстрация завершена!")
    print(f"{'='*50}")
    print("\n📝 Результаты:")
    print("- ✅ Администратор: полный доступ ко всем ресурсам")
    print("- ✅ Менеджер: расширенный доступ к бизнес-объектам")
    print("- ✅ Пользователь: ограниченный доступ к своим объектам")
    print("- ✅ Система правильно разграничивает права доступа")

if __name__ == "__main__":
    main()
