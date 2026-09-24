from django.contrib import admin
from shop.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'phone', 'city']
    list_filter = ['city', 'created_at']
