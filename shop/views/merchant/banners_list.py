from django.shortcuts import render
from .staff_required import staff_required

@staff_required
def banners_list(request):
    return render(request, 'shop/merchant/banners_list.html')