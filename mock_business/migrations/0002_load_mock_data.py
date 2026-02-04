from django.db import migrations
import uuid
from django.db import models


def load_mock_data(apps, schema_editor):
    # Получаем модели
    Shop = apps.get_model('mock_business', 'Shop')
    Product = apps.get_model('mock_business', 'Product')
    Order = apps.get_model('mock_business', 'Order')
    User = apps.get_model('authentication', 'User')
    
    # Получаем или создаем пользователя-менеджера для mock данных
    try:
        manager_user = User.objects.get(email='manager@example.com')
    except User.DoesNotExist:
        manager_user = User.objects.create(
            email='manager@example.com',
            first_name='Mock',
            last_name='Manager',
            is_staff=True,
            is_superuser=False
        )
        manager_user.set_password('manager123')
        manager_user.save()
    
    # Получаем или создаем пользователя-покупателя для mock данных
    try:
        customer_user = User.objects.get(email='user@example.com')
    except User.DoesNotExist:
        customer_user = User.objects.create(
            email='user@example.com',
            first_name='Mock',
            last_name='User',
            is_staff=False,
            is_superuser=False
        )
        customer_user.set_password('user123')
        customer_user.save()
    
    # Mock данные для магазинов
    mock_shops = [
        {
            'id': uuid.uuid4(),
            'name': 'Tech Store Downtown',
            'address': '123 Main St, City',
            'phone': '+1-555-0123',
        },
        {
            'id': uuid.uuid4(),
            'name': 'Gadget World',
            'address': '456 Market St, City',
            'phone': '+1-555-0456',
        }
    ]
    
    # Mock данные для продуктов
    mock_products = [
        {
            'id': uuid.uuid4(),
            'name': 'Laptop Dell XPS 15',
            'description': 'Powerful laptop with 4K display',
            'price': 1999.99,
        },
        {
            'id': uuid.uuid4(),
            'name': 'iPhone 15 Pro',
            'description': 'Latest iPhone with titanium design',
            'price': 1199.99,
        },
        {
            'id': uuid.uuid4(),
            'name': 'Samsung Galaxy S24',
            'description': 'Latest Samsung flagship phone',
            'price': 999.99,
        },
        {
            'id': uuid.uuid4(),
            'name': 'iPad Pro 12.9"',
            'description': 'Professional tablet with M2 chip',
            'price': 1499.99,
        },
        {
            'id': uuid.uuid4(),
            'name': 'MacBook Air M2',
            'description': 'Thin and light laptop with M2 chip',
            'price': 1299.99,
        },
        {
            'id': uuid.uuid4(),
            'name': 'AirPods Pro 2',
            'description': 'Wireless earbuds with noise cancellation',
            'price': 249.99,
        }
    ]
    
    # Mock данные для заказов
    mock_orders = [
        {
            'id': uuid.uuid4(),
            'quantity': 1,
            'status': 'pending',
        },
        {
            'id': uuid.uuid4(),
            'quantity': 2,
            'status': 'completed',
        },
        {
            'id': uuid.uuid4(),
            'quantity': 1,
            'status': 'pending',
        }
    ]
    
    # Создаем магазины
    shops = []
    for shop_data in mock_shops:
        shop = Shop.objects.create(
            id=shop_data['id'],
            name=shop_data['name'],
            address=shop_data['address'],
            phone=shop_data['phone'],
            owner=manager_user  # Назначаем менеджера
        )
        shops.append(shop)
    
    # Создаем продукты и привязываем к магазинам
    products = []
    for i, product_data in enumerate(mock_products):
        shop = shops[i % len(shops)]  # Распределяем продукты по магазинам
        product = Product.objects.create(
            id=product_data['id'],
            name=product_data['name'],
            description=product_data['description'],
            price=product_data['price'],
            shop=shop,
            owner=manager_user  # Владелец - менеджер магазина
        )
        products.append(product)
    
    # Создаем заказы
    for i, order_data in enumerate(mock_orders):
        product = products[i % len(products)]  # Распределяем заказы по продуктам
        # Рассчитываем общую стоимость
        total_price = product.price * order_data['quantity']
        Order.objects.create(
            id=order_data['id'],
            product=product,
            quantity=order_data['quantity'],
            total_price=total_price,  # Добавляем расчетную стоимость
            status=order_data['status'],
            customer=customer_user  # Покупатель
        )


def reverse_load_mock_data(apps, schema_editor):
    # Удаляем mock данные
    Shop = apps.get_model('mock_business', 'Shop')
    Product = apps.get_model('mock_business', 'Product')
    Order = apps.get_model('mock_business', 'Order')
    
    # Удаляем все данные (для простоты)
    Order.objects.all().delete()
    Product.objects.all().delete()
    Shop.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('mock_business', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_mock_data, reverse_load_mock_data),
    ]
