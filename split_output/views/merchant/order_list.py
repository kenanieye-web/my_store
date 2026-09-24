from django.shortcuts import render
from shop.models import Order

from shop.views.merchant.staff_required import staff_required


@staff_required
def order_list(request):
    """قائمة جميع الطلبات للتاجر"""
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'shop/order_list.html', {'orders': orders})
