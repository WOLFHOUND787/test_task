from django.urls import path
from . import views

app_name = 'mock_business'

urlpatterns = [
    # Магазины
    path('shops/', views.shop_list_view, name='shop_list'),
    path('shops/create/', views.shop_create_view, name='shop_create'),
    path('shops/<uuid:shop_id>/products/', views.shop_products_view, name='shop_products'),
    path('shops/<uuid:shop_id>/delete/', views.shop_delete_view, name='shop_delete'),
    
    # Продукты
    path('products/', views.product_list_view, name='product_list'),
    path('products/create/', views.product_create_view, name='product_create'),
    
    # Заказы
    path('orders/', views.order_list_view, name='order_list'),
    path('orders/create/', views.order_create_view, name='order_create'),
    path('orders/<uuid:order_id>/complete/', views.order_complete_view, name='order_complete'),
    path('orders/<uuid:order_id>/cancel/', views.order_cancel_view, name='order_cancel'),
    path('orders/<uuid:order_id>/delete/', views.order_delete_view, name='order_delete'),
    
    # Пользователи (только для админа)
    path('users/', views.user_list_view, name='user_list'),
    path('users/<uuid:user_id>/update/', views.user_update_view, name='user_update'),
    path('users/<uuid:user_id>/delete/', views.user_delete_view, name='user_delete'),
    
    # Профиль пользователя
    path('profile/', views.profile_view, name='profile'),
]
