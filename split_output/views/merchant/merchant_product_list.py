from django.shortcuts import render
from shop.models import Product

from shop.views.merchant.staff_required import staff_required


@staff_required
def merchant_product_list(request):
    """إدارة المنتجات للتاجر"""
    products = Product.objects.select_related('category').all().order_by('-id')
    return render(request, 'shop/merchant_product_list.html', {'products': products})
