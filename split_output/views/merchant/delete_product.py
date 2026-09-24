from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from shop.models import Product

from shop.views.merchant.staff_required import staff_required


@staff_required
def delete_product(request, pk):
    """حذف منتج"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f"تم حذف المنتج '{product_name}' بنجاح.")
        return redirect('merchant_product_list')
    return render(request, 'shop/confirm_delete_product.html', {'product': product})
