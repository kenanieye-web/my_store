from django.shortcuts import render
from .staff_required import staff_required

@staff_required
def promotions_list(request):
    return render(request, 'shop/merchant/promotions_list.html')