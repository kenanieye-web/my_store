from django.contrib import admin
from shop.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'customer_type', 'created_at']
    list_editable = ['customer_type']  # تغيير مستوى السعر (تجزئة/جملة/جملة الجملة) مباشرة من القائمة
    search_fields = ['user__username', 'user__first_name', 'phone', 'city']
    list_filter = ['customer_type', 'city', 'created_at']