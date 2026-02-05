from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from authentication.authorization import CustomObjectPermissionFactory
from authentication.models import User
from .models import Shop, Product, Order
import uuid


@api_view(['GET'])
@permission_classes([CustomObjectPermissionFactory('shops', 'read')])
def shop_list_view(request):
    """Получение списка всех магазинов"""
    shops = Shop.objects.filter(is_active=True)
    shop_data = []
    
    for shop in shops:
        shop_data.append({
            'id': str(shop.id),
            'name': shop.name,
            'address': shop.address,
            'phone': shop.phone,
            'owner_id': str(shop.owner.id) if shop.owner else None,
            'created_at': shop.created_at.isoformat()
        })
    
    return Response({'shops': shop_data})


@api_view(['GET'])
@permission_classes([CustomObjectPermissionFactory('shops', 'read')])
def shop_products_view(request, shop_id):
    """Получение продуктов конкретного магазина"""
    try:
        shop = Shop.objects.get(id=shop_id, is_active=True)
        products = Product.objects.filter(shop=shop, is_active=True)
        
        product_data = []
        for product in products:
            product_data.append({
                'id': str(product.id),
                'name': product.name,
                'description': product.description,
                'price': float(product.price),
                'shop_id': str(product.shop.id),
                'owner_id': str(product.owner.id) if product.owner else None,
                'created_at': product.created_at.isoformat()
            })
        
        return Response({'products': product_data})
    except Shop.DoesNotExist:
        return Response({'error': 'Shop not found'}, status=404)


@api_view(['GET'])
@permission_classes([CustomObjectPermissionFactory('products', 'read')])
def product_list_view(request):
    """Получение списка всех продуктов"""
    products = Product.objects.filter(is_active=True)
    product_data = []
    
    for product in products:
        product_data.append({
            'id': str(product.id),
            'name': product.name,
            'description': product.description,
            'price': float(product.price),
            'shop_id': str(product.shop.id),
            'owner_id': str(product.owner.id) if product.owner else None,
            'created_at': product.created_at.isoformat()
        })
    
    return Response({'products': product_data})


@api_view(['DELETE'])
@permission_classes([CustomObjectPermissionFactory('shops', 'delete')])
def shop_delete_view(request, shop_id):
    """Удалить магазин"""
    user = request.user
    
    try:
        shop = Shop.objects.get(id=shop_id)
    except Shop.DoesNotExist:
        return Response({'error': 'Shop not found'}, status=404)
    
    # Проверяем что это владелец магазина или суперпользователь
    if not user.is_superuser and shop.owner != user:
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    # Проверяем что у магазина нет заказов
    if Order.objects.filter(product__shop=shop, status='pending').exists():
        return Response({'error': 'Cannot delete shop with pending orders'}, status=400)
    
    shop.delete()
    
    return Response({'message': 'Shop deleted successfully'})


@api_view(['POST'])
@permission_classes([CustomObjectPermissionFactory('products', 'create')])
def product_create_view(request):
    """Создание нового продукта"""
    user = request.user
    
    # Проверяем что у менеджера есть магазины
    shops = Shop.objects.filter(owner=user, is_active=True)
    if not shops.exists():
        return Response({'error': 'Manager must have a shop to create products'}, status=400)
    
    data = request.data
    if not data.get('name') or not data.get('price'):
        return Response({'error': 'Name and price are required'}, status=400)
    
    # Если у менеджера несколько магазинов, нужно указать shop_id
    shop_id = data.get('shop_id')
    if shops.count() > 1:
        if not shop_id:
            return Response({'error': 'Shop ID is required when manager has multiple shops'}, status=400)
        try:
            shop = shops.get(id=shop_id)
        except Shop.DoesNotExist:
            return Response({'error': 'Invalid shop ID'}, status=400)
    else:
        # Если один магазин, берем его
        shop = shops.first()
    
    product = Product.objects.create(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        shop=shop,
        owner=user
    )
    
    return Response({
        'id': str(product.id),
        'name': product.name,
        'description': product.description,
        'price': float(product.price),
        'shop_id': str(product.shop.id),
        'owner_id': str(product.owner.id),
        'created_at': product.created_at.isoformat()
    }, status=201)


@api_view(['GET'])
@permission_classes([CustomObjectPermissionFactory('orders', 'read')])
def order_list_view(request):
    """Получение списка заказов"""
    user = request.user
    
    if user.is_superuser:
        orders = Order.objects.all()
    elif user.user_roles.filter(role__name='manager').exists():
        # Менеджеры видят заказы на свои продукты
        user_shops = Shop.objects.filter(owner=user)
        orders = Order.objects.filter(product__shop__in=user_shops)
    else:
        # Пользователи видят только свои заказы
        orders = Order.objects.filter(customer=user)
    
    order_data = []
    for order in orders:
        order_data.append({
            'id': str(order.id),
            'product_name': order.product.name,
            'quantity': order.quantity,
            'total_price': float(order.total_price),
            'status': order.status,
            'customer_id': str(order.customer.id) if order.customer else None,
            'created_at': order.created_at.isoformat()
        })
    
    return Response({'orders': order_data})


@api_view(['POST'])
@permission_classes([CustomObjectPermissionFactory('orders', 'create')])
def order_create_view(request):
    """Создание нового заказа"""
    user = request.user
    
    # Проверяем что менеджеры не могут создавать заказы
    if user.user_roles.filter(role__name='manager').exists():
        return Response({'error': 'Managers cannot create orders'}, status=403)
    
    data = request.data
    if not data.get('product_id') or not data.get('quantity'):
        return Response({'error': 'Product ID and quantity are required'}, status=400)
    
    try:
        product = Product.objects.get(id=data['product_id'], is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)
    
    order = Order.objects.create(
        product=product,
        quantity=data['quantity'],
        customer=user
    )
    
    return Response({
        'id': str(order.id),
        'product_name': order.product.name,
        'quantity': order.quantity,
        'total_price': float(order.total_price),
        'status': order.status,
        'customer_id': str(order.customer.id),
        'created_at': order.created_at.isoformat()
    }, status=201)


@api_view(['POST'])
@permission_classes([CustomObjectPermissionFactory('shops', 'create')])
def shop_create_view(request):
    """Создание нового магазина"""
    user = request.user
    
    # Проверяем что только менеджеры могут создавать магазины
    if not user.user_roles.filter(role__name='manager').exists():
        return Response({'error': 'Only managers can create shops'}, status=403)
    
    data = request.data
    if not data.get('name') or not data.get('address') or not data.get('phone'):
        return Response({'error': 'Name, address and phone are required'}, status=400)
    
    shop = Shop.objects.create(
        name=data['name'],
        address=data['address'],
        phone=data['phone'],
        owner=user
    )
    
    return Response({
        'id': str(shop.id),
        'name': shop.name,
        'address': shop.address,
        'phone': shop.phone,
        'owner_id': str(shop.owner.id),
        'created_at': shop.created_at.isoformat()
    }, status=201)


@api_view(['GET'])
@permission_classes([CustomObjectPermissionFactory('users', 'read')])
def user_list_view(request):
    """Получение списка пользователей"""
    users = User.objects.all()
    user_data = []
    
    for user in users:
        roles = [ur.role.name for ur in user.user_roles.all()]
        user_data.append({
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'roles': roles,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        })
    
    return Response({'users': user_data})


@api_view(['GET', 'PUT'])
@permission_classes([CustomObjectPermissionFactory('profiles', 'read')])
def profile_view(request):
    """Просмотр и обновление профиля"""
    user = request.user
    
    if request.method == 'GET':
        roles = [ur.role.name for ur in user.user_roles.all()]
        return Response({
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'patronymic': user.patronymic,
            'roles': roles,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        })
    
    elif request.method == 'PUT':
        data = request.data
        # Обновляем только first_name и last_name, email не меняем
        if 'full_name' in data:
            full_name = data['full_name']
            # Разделяем полное имя на части
            name_parts = full_name.split(' ', 2)
            user.first_name = name_parts[1] if len(name_parts) > 1 else ''
            user.last_name = name_parts[0] if len(name_parts) > 0 else ''
            user.patronymic = name_parts[2] if len(name_parts) > 2 else ''
        
        user.save()
        
        roles = [ur.role.name for ur in user.user_roles.all()]
        return Response({
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'patronymic': user.patronymic,
            'roles': roles,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        })


@api_view(['PUT'])
@permission_classes([CustomObjectPermissionFactory('orders', 'update')])
def order_complete_view(request, order_id):
    """Выполнить заказ"""
    user = request.user
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    
    # Проверяем что менеджер может выполнять заказы на свои продукты
    if not user.is_superuser:
        user_shops = Shop.objects.filter(owner=user)
        if not Order.objects.filter(id=order_id, product__shop__in=user_shops).exists():
            return Response({'error': 'Insufficient permissions'}, status=403)
    
    if order.status != 'pending':
        return Response({'error': 'Order cannot be completed'}, status=400)
    
    order.status = 'completed'
    order.save()
    
    return Response({
        'id': str(order.id),
        'product_name': order.product.name,
        'quantity': order.quantity,
        'total_price': float(order.total_price),
        'status': order.status,
        'customer_id': str(order.customer.id),
        'created_at': order.created_at.isoformat()
    })


@api_view(['PUT'])
@permission_classes([CustomObjectPermissionFactory('orders', 'update')])
def order_cancel_view(request, order_id):
    """Отменить заказ"""
    user = request.user
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    
    # Проверяем права: только владелец заказа может отменить (менеджеры не могут)
    if not user.is_superuser:
        # Только владелец заказа может отменить
        if order.customer != user:
            return Response({'error': 'Insufficient permissions'}, status=403)
    
    if order.status != 'pending':
        return Response({'error': 'Order cannot be cancelled'}, status=400)
    
    order.status = 'cancelled'
    order.save()
    
    return Response({
        'id': str(order.id),
        'product_name': order.product.name,
        'quantity': order.quantity,
        'total_price': float(order.total_price),
        'status': order.status,
        'customer_id': str(order.customer.id),
        'created_at': order.created_at.isoformat()
    })


@api_view(['DELETE'])
@permission_classes([CustomObjectPermissionFactory('orders', 'delete')])
def order_delete_view(request, order_id):
    """Удалить заказ (только отмененные заказы и только для владельцев)"""
    user = request.user
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    
    # Проверяем что это владелец заказа или суперпользователь
    if order.customer != user and not user.is_superuser:
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    # Проверяем что заказ отменен
    if order.status != 'cancelled':
        return Response({'error': 'Only cancelled orders can be deleted'}, status=400)
    
    order.delete()
    
    return Response({'message': 'Order deleted successfully'})


@api_view(['PUT'])
@permission_classes([CustomObjectPermissionFactory('users', 'update')])
def user_update_view(request, user_id):
    """Обновить пользователя (только для админа)"""
    user = request.user
    
    if not user.is_superuser:
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
    
    # Нельзя изменять суперпользователя
    if target_user.is_superuser:
        return Response({'error': 'Cannot modify superuser'}, status=403)
    
    data = request.data
    
    # Обновляем поля
    if 'full_name' in data:
        # full_name это property, его нужно вычислять из first_name и last_name
        names = data['full_name'].split()
        target_user.first_name = names[0] if names else ''
        target_user.last_name = ' '.join(names[1:]) if len(names) > 1 else ''
    
    if 'is_active' in data:
        target_user.is_active = data['is_active']
    
    if 'ban_until' in data:
        # Здесь можно добавить логику бана в модели User
        pass
    
    target_user.save()
    
    return Response({
        'message': 'User updated successfully',
        'user': {
            'id': str(target_user.id),
            'email': target_user.email,
            'full_name': target_user.full_name,
            'is_active': target_user.is_active,
            'roles': [ur.role.name for ur in target_user.user_roles.all()]
        }
    })


@api_view(['DELETE'])
@permission_classes([CustomObjectPermissionFactory('users', 'delete')])
def user_delete_view(request, user_id):
    """Удалить пользователя (только для админа)"""
    user = request.user
    
    if not user.is_superuser:
        return Response({'error': 'Insufficient permissions'}, status=403)
    
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
    
    # Нельзя удалять суперпользователя
    if target_user.is_superuser:
        return Response({'error': 'Cannot delete superuser'}, status=403)
    
    # Нельзя удалять самого себя
    if target_user == user:
        return Response({'error': 'Cannot delete yourself'}, status=403)
    
    target_user.delete()
    
    return Response({'message': 'User deleted successfully'})
