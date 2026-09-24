from django.contrib import admin
from shop.models import Order

from shop.admin.order_item_inline import OrderItemInline


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'city', 'phone', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    inlines = [OrderItemInline]
