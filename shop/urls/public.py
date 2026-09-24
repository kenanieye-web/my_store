from django.urls import path
from shop.views import product_views  # أو استيراد الملف الذي توجد فيه دالة product_list مباشرة

app_name = 'shop'

urlpatterns = [
    # مسار عرض جميع المنتجات (الرئيسية)
    path('', product_views.product_list, name='product_list'),
    
    # مسار عرض المنتجات الخاصة بتصنيف معين عبر الـ slug
    path('category/<slug:category_slug>/', product_views.product_list, name='product_list_by_category'),
]