from django.urls import path
from shop.views.public import home, product_list, product_detail, live_search
from shop.views.cart import cart_detail, add_to_cart, remove_from_cart, update_cart_quantity
from shop.views.orders import checkout, order_success
from shop.views.account import register_user, login_user, logout_user, customer_profile
from ..views.merchant import edit_product
# استيراد دوال لوحة تحكم التاجر بالشكل الصحيح (كل دالة من ملفها)
from shop.views.merchant.merchant_dashboard import merchant_dashboard
from shop.views.merchant.merchant_product_list import merchant_product_list
from shop.views.merchant.add_product import add_product
from shop.views.merchant.order_list import order_list
from shop.views.merchant.order_detail import order_detail
from shop.views.merchant.customer_list import customer_list
from shop.views.merchant.sales_report import sales_report
from shop.views.merchant.download_template import download_template
from shop.views.merchant.import_excel import import_excel
from shop.views.merchant.import_excel import import_product_from_url
from shop.views.merchant.staff_user_list import staff_user_list
from shop.views.merchant.coupons import merchant_coupons_list
from shop.views.merchant import delete_product
from shop.views.merchant.category_list import merchant_category_list
from shop.views.merchant.export_orders import (
    export_orders_excel, 
    export_orders_pdf, 
    export_single_order_excel, 
    export_single_order_pdf

)
# مسارات جديدة: المخزون، الشحن، الدفع
from shop.views.merchant.inventory import inventory_list
from shop.views.merchant.shipping import shipping_list
from shop.views.merchant.payment import payment_list

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
    path('order-success/<int:order_id>/', order_success, name='order_success'),

    # مسارات الحسابات والعملاء
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),  
    path('logout-user/', logout_user, name='logout_user'), 
    path('profile/', customer_profile, name='customer_profile'),

    # مسارات لوحة تحكم التجار (كاملة ومرتبة)
    path('merchant/dashboard/', merchant_dashboard, name='merchant_dashboard'),
    path('merchant/products/', merchant_product_list, name='merchant_product_list'),
    path('merchant/products/add/', add_product, name='add_product'),
    path('merchant/products/<int:pk>/edit/', edit_product, name='edit_product'),
    path('merchant/orders/', order_list, name='order_list'),
    path('merchant/customers/', customer_list, name='customer_list'),
    path('merchant/sales-report/', sales_report, name='sales_report'),
    path('merchant/staff/', staff_user_list, name='staff_user_list'),
    path('merchant/orders/<int:pk>/', order_detail, name='order_detail'),
    path('merchant/products/import-url/', import_product_from_url, name='import_product_from_url'),
    path('merchant/categories/', merchant_category_list, name='merchant_category_list'),
    path('merchant/coupons/', merchant_coupons_list, name='merchant_coupons_list'),
    path('merchant/product/delete/<int:pk>/', delete_product, name='delete_product'),
    #path('merchant/promotions/', promotions_list, name='promotions_list'),
    #path('merchant/loyalty/', loyalty_program, name='loyalty_program'),
    #path('merchant/banners/', banners_list, name='banners_list'),
    #path('merchant/affiliate/', affiliate_marketing, name='affiliate_marketing'),
    # مسارات استيراد وتصدير المنتجات (مطابقة لأسماء القالب بـ dash)
    path('merchant/products/download-template/', download_template, name='download-template'),
    path('merchant/products/import-excel/', import_excel, name='import-excel'),

    # مسارات تصدير جميع الطلبات (Excel / PDF)
    path('merchant/orders/export/excel/', export_orders_excel, name='export_orders_excel'),
    path('merchant/orders/export/pdf/', export_orders_pdf, name='export_orders_pdf'),
    
    # مسارات تصدير طلب واحد محدد (Excel / PDF)
    path('merchant/orders/export/<int:order_id>/excel/', export_single_order_excel, name='export_single_order_excel'),
    path('merchant/orders/export/<int:order_id>/pdf/', export_single_order_pdf, name='export_single_order_pdf'),

    # مسارات جديدة: المخزون، الشحن، الدفع
    path('merchant/inventory/', inventory_list, name='inventory_list'),
    path('merchant/shipping/', shipping_list, name='shipping_settings'),
    path('merchant/payments/', payment_list, name='payment_settings'),

    # مسارات التواصل
    path('contact/', home, name='contact_us'), 
]