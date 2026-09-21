from django.contrib import admin
from .models import Category, Product, ProductImage, Cart, CartItem, Order, OrderItem, Customer
import openpyxl
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import render, redirect



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


# 4. تخصيص عرض المنتجات مع إضافة معرض الصور والبحث المتقدم واستيراد/تصدير Excel
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_available', 'created_at']
    list_filter = ['is_available', 'category', 'created_at']
    list_editable = ['price', 'stock', 'is_available']
    search_fields = ['name', 'model', 'description', 'specifications']
    inlines = [ProductImageInline]
    actions = ['export_to_excel']
    change_list_template = "admin/product_changelist.html"

    def export_to_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Products"
        ws.append(['ID', 'الاسم', 'التصنيف', 'الموديل', 'السعر', 'المخزون',
                    'متوفر', 'الوصف', 'المواصفات'])

        for p in queryset:
            ws.append([
                p.id, p.name, p.category.name if p.category else '',
                p.model, float(p.price), p.stock,
                'نعم' if p.is_available else 'لا',
                p.description, p.specifications,
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=products.xlsx'
        wb.save(response)
        return response
    export_to_excel.short_description = "تصدير المنتجات المحددة إلى Excel"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.import_excel, name='product-import-excel'),
        ]
        return custom_urls + urls

    def import_excel(self, request):
        if request.method == "POST":
            excel_file = request.FILES["excel_file"]
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active

            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row[0] and not row[1]:
                    continue
                product_id, name, category_name, model_, price, stock, is_available, description, specifications = row

                category_obj = None
                if category_name:
                    category_obj, _ = Category.objects.get_or_create(name=category_name)

                Product.objects.update_or_create(
                    id=product_id if product_id else None,
                    defaults={
                        'name': name,
                        'category': category_obj,
                        'model': model_,
                        'price': price,
                        'stock': stock or 0,
                        'is_available': str(is_available).strip() in ['نعم', 'True', 'true', '1'],
                        'description': description or '',
                        'specifications': specifications or '',
                    }
                )
            self.message_user(request, "تم استيراد المنتجات بنجاح")
            return redirect("..")

        return render(request, "admin/excel_import.html")

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