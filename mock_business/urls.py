from django.urls import path
from . import views

app_name = 'mock_business'

urlpatterns = [
    # Продукты
    path('products/', views.product_list_view, name='product_list'),
    path('products/create/', views.product_create_view, name='product_create'),
    
    # Заказы
    path('orders/', views.order_list_view, name='order_list'),
    path('orders/create/', views.order_create_view, name='order_create'),
    
    # Магазины
    path('shops/', views.shop_list_view, name='shop_list'),
    path('shops/create/', views.shop_create_view, name='shop_create'),
    
    # Пользователи
    path('users/', views.user_list_view, name='user_list'),
    
    # Отчеты
    path('reports/', views.reports_view, name='reports'),
]
