from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render

from shop.forms import ProductForm
from shop.models.product_image import ProductImage
from shop.views.merchant.staff_required import staff_required


@staff_required
def add_product(request):
    """إضافة منتج جديد"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                product = form.save()
                for f in form.cleaned_data['gallery']:
                    ProductImage.objects.create(product=product, image=f)
            messages.success(request, "تم إضافة المنتج بنجاح!")
            return redirect('merchant_product_list')
    else:
        form = ProductForm()
    return render(request, 'shop/merchant/add_product.html', {'form': form, 'max_gallery': 5})