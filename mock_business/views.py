from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from authentication.authorization import CustomObjectPermission
from authentication.models import User
import uuid


# Mock данные для демонстрации
MOCK_PRODUCTS = [
    {
        'id': str(uuid.uuid4()),
        'name': 'Laptop Dell XPS 15',
        'description': 'Powerful laptop with 4K display',
        'price': 1999.99,
        'owner_id': None,  # Публичный продукт
        'created_at': '2024-01-15T10:30:00Z'
    },
    {
        'id': str(uuid.uuid4()),
        'name': 'iPhone 15 Pro',
        'description': 'Latest iPhone with titanium design',
        'price': 1199.99,
        'owner_id': None,  # Публичный продукт
        'created_at': '2024-01-20T14:15:00Z'
    }
]

MOCK_ORDERS = [
    {
        'id': str(uuid.uuid4()),
        'product_name': 'Laptop Dell XPS 15',
        'quantity': 1,
        'total_price': 1999.99,
        'status': 'completed',
        'owner_id': None,  # Будет установлен при создании
        'created_at': '2024-01-16T09:45:00Z'
    }
]

MOCK_SHOPS = [
    {
        'id': str(uuid.uuid4()),
        'name': 'Tech Store Downtown',
        'address': '123 Main St, City',
        'phone': '+1-555-0123',
        'owner_id': None,  # Публичный магазин
        'created_at': '2024-01-01T00:00:00Z'
    }
]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_list_view(request):
    """Список продуктов"""
    from authentication.authorization import check_user_permission
    
    # Проверяем права на чтение продуктов
    if not check_user_permission(request.user, 'products', 'read'):
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    user = request.user
    
    # Фильтруем продукты в зависимости от прав
    products = []
    for product in MOCK_PRODUCTS:
        if product['owner_id'] is None:
            # Публичные продукты доступны всем
            products.append(product)
        elif str(product['owner_id']) == str(user.id):
            # Продукты пользователя доступны ему
            products.append(product)
        else:
            # Проверяем права на чтение всех продуктов
            if check_user_permission(user, 'products', 'read_all'):
                products.append(product)
    
    return Response({'products': products})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_create_view(request):
    """Создание продукта"""
    from authentication.authorization import check_user_permission
    
    # Проверяем права на создание продуктов
    if not check_user_permission(request.user, 'products', 'create'):
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    product_data = request.data
    new_product = {
        'id': str(uuid.uuid4()),
        'name': product_data.get('name', 'New Product'),
        'description': product_data.get('description', ''),
        'price': product_data.get('price', 0.0),
        'owner_id': str(request.user.id),  # Владелец - текущий пользователь
        'created_at': '2024-01-25T12:00:00Z'
    }
    
    MOCK_PRODUCTS.append(new_product)
    return Response(new_product, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list_view(request):
    """Список заказов"""
    from authentication.authorization import check_user_permission
    
    # Проверяем права на чтение заказов
    if not check_user_permission(request.user, 'orders', 'read'):
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    user = request.user
    
    orders = []
    for order in MOCK_ORDERS:
        if order['owner_id'] is None:
            orders.append(order)
        elif str(order['owner_id']) == str(user.id):
            orders.append(order)
        else:
            from authentication.authorization import check_user_permission
            if check_user_permission(user, 'orders', 'read_all'):
                orders.append(order)
    
    return Response({'orders': orders})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_create_view(request):
    """Создание заказа"""
    from authentication.authorization import check_user_permission
    
    # Проверяем права на создание заказов
    if not check_user_permission(request.user, 'orders', 'create'):
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    order_data = request.data
    new_order = {
        'id': str(uuid.uuid4()),
        'product_name': order_data.get('product_name', 'Unknown Product'),
        'quantity': order_data.get('quantity', 1),
        'total_price': order_data.get('total_price', 0.0),
        'status': 'pending',
        'owner_id': str(request.user.id),
        'created_at': '2024-01-25T12:00:00Z'
    }
    
    MOCK_ORDERS.append(new_order)
    return Response(new_order, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shop_list_view(request):
    """Список магазинов"""
    from authentication.authorization import check_user_permission
    
    # Проверяем права на чтение магазинов
    if not check_user_permission(request.user, 'shops', 'read'):
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    user = request.user
    
    shops = []
    for shop in MOCK_SHOPS:
        if shop['owner_id'] is None:
            shops.append(shop)
        elif str(shop['owner_id']) == str(user.id):
            shops.append(shop)
        else:
            from authentication.authorization import check_user_permission
            if check_user_permission(user, 'shops', 'read_all'):
                shops.append(shop)
    
    return Response({'shops': shops})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shop_create_view(request):
    """Создание магазина"""
    from authentication.authorization import check_user_permission
    
    # Проверяем права на создание магазинов
    if not check_user_permission(request.user, 'shops', 'create'):
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    shop_data = request.data
    new_shop = {
        'id': str(uuid.uuid4()),
        'name': shop_data.get('name', 'New Shop'),
        'address': shop_data.get('address', ''),
        'phone': shop_data.get('phone', ''),
        'owner_id': str(request.user.id),
        'created_at': '2024-01-25T12:00:00Z'
    }
    
    MOCK_SHOPS.append(new_shop)
    return Response(new_shop, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list_view(request):
    """Список пользователей (только для демонстрации)"""
    from authentication.authorization import check_user_permission
    
    # Проверяем права на чтение пользователей
    if not check_user_permission(request.user, 'users', 'read'):
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    users = User.objects.filter(is_active=True).values('id', 'email', 'first_name', 'last_name', 'created_at')
    return Response({'users': list(users)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reports_view(request):
    """Отчеты (демонстрация сложного ресурса)"""
    from authentication.authorization import check_user_permission
    
    # Проверяем права на чтение отчетов
    if not check_user_permission(request.user, 'reports', 'read'):
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    return Response({
        'message': 'Access granted to reports',
        'available_reports': [
            'sales_report',
            'user_activity_report',
            'inventory_report'
        ],
        'generated_at': '2024-01-25T12:00:00Z'
    })
