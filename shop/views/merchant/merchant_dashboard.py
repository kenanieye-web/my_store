from django.shortcuts import render
from shop.models import Product, Order, Customer
from django.db.models import Q

from shop.views.merchant.staff_required import staff_required


@staff_required
def merchant_dashboard(request):
    """لوحة التحكم العامة للتاجر والإحصائيات السريعة"""
    products_count = Product.objects.count()
    customers_count = Customer.objects.count()
    total_orders_count = Order.objects.count()

    new_orders_count = Order.objects.filter(Q(status='new') | Q(status='جديد')).count()
    shipping_orders_count = Order.objects.filter(Q(status__in=['shipping', 'قيد الشحن', 'جاري الشحن', 'التوصيل'])).count()
    delivered_orders_count = Order.objects.filter(Q(status='delivered') | Q(status='تم التوصيل')).count()
    canceled_orders_count = Order.objects.filter(Q(status='canceled') | Q(status='ملغي') | Q(status='الملغية')).count()

    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    context = {
        'products_count': products_count,
        'customers_count': customers_count,
        'total_orders_count': total_orders_count,
        'new_orders_count': new_orders_count,
        'shipping_orders_count': shipping_orders_count,
        'delivered_orders_count': delivered_orders_count,
        'canceled_orders_count': canceled_orders_count,
        'recent_orders': recent_orders,
    }
    return render(request, 'shop/dashboard.html', context)
