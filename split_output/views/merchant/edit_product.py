from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from shop.models import Product
from shop.forms import ProductForm

from shop.views.merchant.staff_required import staff_required


@staff_required
def edit_product(request, pk):
    """تعديل بيانات منتج قائمة"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"تم تحديث المنتج '{product.name}' بنجاح!")
            return redirect('merchant_product_list')
    else:
        form = ProductForm(instance=product)
        
    return render(request, 'shop/edit_product.html', {'form': form, 'product': product})
