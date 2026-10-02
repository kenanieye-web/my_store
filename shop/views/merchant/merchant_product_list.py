from django.shortcuts import render
from shop.models import PricingSettings, Product

from shop.views.merchant.staff_required import staff_required


@staff_required
def merchant_product_list(request):
    """إدارة المنتجات للتاجر"""
    products = list(Product.objects.select_related('category').all().order_by('-id'))
    pricing = PricingSettings.get_solo()  # استعلام واحد بدل استعلام لكل منتج
    for p in products:
        p.retail_p = p.get_price('retail', pricing)
        p.wholesale_p = p.get_price('wholesale', pricing)
        p.super_p = p.get_price('super_wholesale', pricing)
    return render(request, 'shop/merchant/merchant_product_list.html', {'products': products})