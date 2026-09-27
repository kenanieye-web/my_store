from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from shop.models import ProductRequest, ProductRequestImage

MAX_IMAGES = 5

@login_required(login_url='login')
def request_product(request):
    """صفحة طلب منتج غير متوفر في المتجر"""
    customer = getattr(request.user, 'customer_profile', None)
    default_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    default_phone = getattr(customer, 'phone', '') if customer else ''
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        product_name = request.POST.get('product_name', '').strip()
        specifications = request.POST.get('specifications', '').strip()
        quantity = request.POST.get('quantity') or 1
        approximate_price = request.POST.get('approximate_price') or None
        video_url = request.POST.get('video_url', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not full_name or not phone or not product_name:
            messages.error(request, 'الاسم ورقم الهاتف واسم المنتج حقول مطلوبة')
        else:
            customer = None
            if request.user.is_authenticated:
                customer = getattr(request.user, 'customer_profile', None)

            product_request = ProductRequest.objects.create(
                customer=customer,
                full_name=default_name,
                phone=default_phone,
                product_name=product_name,
                specifications=specifications,
                quantity=quantity,
                approximate_price=approximate_price,
                video_url=video_url,
                notes=notes,
            )

            uploaded_images = request.FILES.getlist('images')[:MAX_IMAGES]
            for img in uploaded_images:
                ProductRequestImage.objects.create(request=product_request, image=img)

            messages.success(request, 'تم استلام طلبك بنجاح، سنتواصل معك عند توفر المنتج')
            return redirect('request_product')
    context = {
    'default_name': default_name,
    'default_phone': default_phone,
      }
    return render(request, 'shop/public/request_product.html', context)