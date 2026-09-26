from django.shortcuts import render, get_object_or_404
from shop.models import Order

def order_success(request, order_id):
    # جلب الطلب بناءً على رقم الـ ID والتأكد أنه يخص المستخدم الحالي (أو حسب نظام متجرك)
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
    }
    return render(request, 'shop/order_success.html', context)