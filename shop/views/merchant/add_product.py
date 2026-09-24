from django.shortcuts import render, redirect
from django.contrib import messages
from shop.forms import ProductForm

from shop.views.merchant.staff_required import staff_required


@staff_required
def add_product(request):
    """إضافة منتج جديد"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "تم إضافة المنتج بنجاح!")
            return redirect('merchant_product_list')
    else:
        form = ProductForm()
    
    return render(request, 'shop/add_product.html', {'form': form})
