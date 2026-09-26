from django.shortcuts import render
from .staff_required import staff_required

@staff_required
def loyalty_program(request):
    return render(request, 'shop/merchant/loyalty_program.html')