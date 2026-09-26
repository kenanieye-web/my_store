from django.shortcuts import render, redirect
from shop.models.coupon import Coupon
from shop.views.merchant.staff_required import staff_required

@staff_required
def merchant_coupons_list(request):
    """إدارة وعرض الكوبونات والعروض التسويقية للتاجر"""
    coupons = Coupon.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        code = request.POST.get('code')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        valid_to = request.POST.get('valid_to')
        
        if code and discount_value and valid_to:
            Coupon.objects.create(
                code=code,
                discount_type=discount_type,
                discount_value=discount_value,
                valid_to=valid_to
            )
            return redirect('merchant_coupons_list')
            
    context = {
        'coupons': coupons,
    }
    return render(request, 'shop/merchant_coupons_list.html', context)
