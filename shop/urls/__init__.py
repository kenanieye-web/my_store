from django.urls import path
from shop.views.public import home, product_list, product_detail, live_search
from shop.views.cart import cart_detail, add_to_cart, remove_from_cart, update_cart_quantity
from shop.views.orders import checkout
from shop.views.account import register_user, login_user, logout_user, customer_profile
from shop.views.merchant import merchant_dashboard

urlpatterns = [
    # المسارات العامة
    path('', home, name='home'),
    path('products/', product_list, name='product_list'),
    path('products/<int:pk>/', product_detail, name='product_detail'),
    path('product/<int:pk>/', product_detail, name='product_detail_single'),
    path('search/', live_search, name='live_search'),
    
    # مسارات سلة المشتريات
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', update_cart_quantity, name='update_cart_quantity'),
    
    # مسارات الطلبات
    path('checkout/', checkout, name='checkout'),
    
    # مسارات الحسابات والعملاء
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login_user'),
    path('logout/', logout_user, name='logout'),  # تم تعديل الاسم ليتطابق مع القالب
    path('logout-user/', logout_user, name='logout_user'), # الاحتفاظ بالاسم القديم كاحتياط
    path('profile/', customer_profile, name='customer_profile'),

    # مسارات التجار
    path('merchant/dashboard/', merchant_dashboard, name='merchant_dashboard'),
    # مسارات التواصل (إذا كانت مدمجة في صفحة عامة أو تخصيص دعم)
    # يمكنك توجيهها للدعم أو الصفحة الرئيسية مؤقتاً لحين ربطها بقالب التواصل
    path('contact/', home, name='contact_us'), # استبدلها بدالة الـ contact إذا كانت موجودة لديك

]