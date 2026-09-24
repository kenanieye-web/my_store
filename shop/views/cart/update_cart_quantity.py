from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from shop.models import CartItem


def update_cart_quantity(request, item_id):
    """زيادة أو إنقاص كمية عنصر داخل السلة"""
    if request.method != 'POST':
        return redirect('cart_detail')

    cart_id = request.session.get('cart_id')
    cart_item = get_object_or_404(CartItem, id=item_id, cart_id=cart_id)
    action = request.POST.get('action')
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"تم تحديث كمية '{cart_item.product.name}'.")
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, f"تم تحديث كمية '{cart_item.product.name}'.")
        else:
            product_name = cart_item.product.name
            cart_item.delete()
            messages.info(request, f"تم حذف '{product_name}' من سلة التسوق.")
            
    return redirect('cart_detail')
