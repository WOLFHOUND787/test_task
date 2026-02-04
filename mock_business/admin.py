from django.contrib import admin
from django.utils.html import format_html
from .models import Shop, Product, Order


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'address', 'phone')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'address', 'phone', 'owner')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop', 'price', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active', 'shop', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'price', 'shop', 'owner')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('shop', 'owner')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Фильтруем магазины по владельцу
        if 'shop' in form.base_fields:
            if request.user.is_superuser:
                form.base_fields['shop'].queryset = Shop.objects.all()
            else:
                form.base_fields['shop'].queryset = Shop.objects.filter(owner=request.user)
        return form


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'quantity', 'total_price', 'status_badge', 'customer', 'created_at')
    list_filter = ('status', 'created_at', 'product__shop')
    search_fields = ('product__name', 'customer__email')
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('product', 'quantity', 'customer')
        }),
        ('Статус и стоимость', {
            'fields': ('status', 'total_price')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'cancelled': '#dc3545'
        }
        labels = {
            'pending': 'В обработке',
            'completed': 'Выполнен',
            'cancelled': 'Отменен'
        }
        color = colors.get(obj.status, '#6c757d')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Статус'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'customer', 'product__shop')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Фильтруем продукты по магазину менеджера
        if 'product' in form.base_fields and not request.user.is_superuser:
            user_shops = Shop.objects.filter(owner=request.user)
            form.base_fields['product'].queryset = Product.objects.filter(shop__in=user_shops)
        return form
