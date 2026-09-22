from django.urls import path
from . import views

urlpatterns = [
    # الرئيسية والمنتجات
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    
    # سلة التسوق والدفع
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    
    # التقارير والدش بورد
    path('dashboard/sales/', views.sales_report, name='sales_report'),
    
    # مسارات نظام تسجيل المستخدمين والحسابات
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.customer_profile, name='customer_profile'),
    
    path('dashboard/', views.merchant_dashboard, name='merchant_dashboard'),
    
    # مسارات إدارة العملاء والمستخدمين للتاجر
    path('dashboard/customers/', views.customer_list, name='customer_list'),
    path('dashboard/staff/', views.staff_user_list, name='staff_user_list'),
    
    # مسارات إدارة الطلبات
    path('dashboard/orders/', views.order_list, name='order_list'),
    path('dashboard/orders/<int:pk>/', views.order_detail, name='order_detail'),

    # مسارات إدارة المنتجات للتاجر
    path('merchant/products/', views.merchant_product_list, name='merchant_product_list'),
    path('merchant/products/add/', views.add_product, name='add_product'),
    path('merchant/products/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('merchant/products/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('merchant/import-product/', views.import_product_from_url, name='import_product_from_url'),
]   