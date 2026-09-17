from django.contrib import admin
from .models import Category, Product, ProductImage, Cart, CartItem, Order, OrderItem, Customer


# 1. تخصيص عرض التصنيفات
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug']
    list_filter = ['parent']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


# 2. تخصيص عرض العملاء
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'phone', 'city']
    list_filter = ['city', 'created_at']


# 3. إتاحة رفع صور متعددة للمنتج داخل صفحة المنتج
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # يعرض 3 حقول فارغة لإضافة صور إضافية
    verbose_name = "صورة إضافية"
    verbose_name_plural = "معرض الصور الإضافية"


# 4. تخصيص عرض المنتجات مع إضافة معرض الصور والبحث المتقدم
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_available', 'created_at']
    list_filter = ['is_available', 'category', 'created_at']
    list_editable = ['price', 'stock', 'is_available']
    search_fields = ['name', 'model', 'description', 'specifications']
    inlines = [ProductImageInline]  # إضافة قسم معرض الصور الإضافية


# 5. تخصيص عرض الطلبات وعناصرها
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'city', 'phone', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    inlines = [OrderItemInline]


# 6. تسجيل باقي النماذج
admin.site.register(Cart)
admin.site.register(CartItem)