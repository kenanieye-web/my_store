from django.shortcuts import render
from shop.models import Order, Customer
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def customer_profile(request):
    """عرض لوحة تحكم وسجل طلبات العميل"""
    customer, created = Customer.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'customer': customer,
        'orders': orders,
    }
    return render(request, 'shop/customer_profile.html', context)
