from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from shop.models import Product, Cart, CartItem
from django.db import transaction


@transaction.atomic
def add_to_cart(request, product_id):
    """إضافة منتج إلى سلة التسوق أو تحديث الكمية"""
    if request.method != 'POST':
        return redirect('product_list')

    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart_id = request.session.get('cart_id')
    
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        if not cart:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    messages.success(request, f"تمت إضافة '{product.name}' إلى سلة التسوق بنجاح.")
    return redirect('cart_detail')
