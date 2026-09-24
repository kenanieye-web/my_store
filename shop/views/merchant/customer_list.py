from django.shortcuts import render
from shop.models import Customer

from shop.views.merchant.staff_required import staff_required


@staff_required
def customer_list(request):
    """عرض قائمة العملاء والبيانات المرتبطة بهم"""
    customers = Customer.objects.select_related('user').all().order_by('-id')
    return render(request, 'shop/customer_list.html', {'customers': customers})
