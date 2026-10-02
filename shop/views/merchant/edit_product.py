from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from shop.models import Product
from shop.models.product_image import ProductImage
from shop.forms import ProductForm
from shop.forms.product_form import MAX_GALLERY_IMAGES
from shop.views.merchant.staff_required import staff_required


@staff_required
def edit_product(request, pk):
    """تعديل بيانات منتج قائم"""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        delete_ids = [i for i in request.POST.getlist('delete_images') if i.isdigit()]
        if form.is_valid():
            new_files = form.cleaned_data['gallery']
            remaining = product.images.exclude(pk__in=delete_ids).count()
            if remaining + len(new_files) > MAX_GALLERY_IMAGES:
                form.add_error('gallery',
                               f"الحد الأقصى {MAX_GALLERY_IMAGES} صور إضافية، المتبقي لك {max(MAX_GALLERY_IMAGES - remaining, 0)}.")
            else:
                with transaction.atomic():
                    product = form.save()
                    for img in product.images.filter(pk__in=delete_ids):
                        img.image.delete(save=False)
                        img.delete()
                    for f in new_files:
                        ProductImage.objects.create(product=product, image=f)
                messages.success(request, f"تم تحديث المنتج '{product.name}' بنجاح!")
                return redirect('merchant_product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'shop/merchant/edit_product.html', {
        'form': form,
        'product': product,
        'gallery': product.images.all(),
        'max_gallery': MAX_GALLERY_IMAGES,
    })