from django.shortcuts import render
from .staff_required import staff_required

@staff_required
def affiliate_marketing(request):
    return render(request, 'shop/merchant/affiliate_marketing.html')
