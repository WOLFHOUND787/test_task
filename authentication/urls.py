from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Аутентификация пользователей
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('refresh/', views.refresh_token_view, name='refresh_token'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('delete-account/', views.delete_account_view, name='delete_account'),
    
    # Просмотр прав доступа
    path('permissions/', views.user_permissions_view, name='user_permissions'),
    
    # Admin API для управления ролями
    path('admin/roles/', views.RoleListCreateView.as_view(), name='role_list_create'),
    path('admin/roles/<uuid:pk>/', views.RoleDetailView.as_view(), name='role_detail'),
    
    # Admin API для управления бизнес-элементами
    path('admin/business-elements/', views.BusinessElementListCreateView.as_view(), name='business_element_list_create'),
    
    # Admin API для управления правилами доступа
    path('admin/access-rules/', views.AccessRoleRuleListCreateView.as_view(), name='access_rule_list_create'),
    path('admin/access-rules/<uuid:pk>/', views.AccessRoleRuleDetailView.as_view(), name='access_rule_detail'),
    
    # Admin API для управления ролями пользователей
    path('admin/user-roles/', views.UserRoleListCreateView.as_view(), name='user_role_list_create'),
    path('admin/user-roles/<uuid:pk>/', views.UserRoleDetailView.as_view(), name='user_role_detail'),
]
