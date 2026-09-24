from django.contrib import admin
from shop.models import ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    verbose_name = "صورة إضافية"
    verbose_name_plural = "معرض الصور الإضافية"
