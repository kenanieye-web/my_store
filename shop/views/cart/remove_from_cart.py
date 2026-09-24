from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from shop.models import CartItem


def remove_from_cart(request, item_id):
    """حذف عنصر محدد من السلة"""
    cart_id = request.session.get('cart_id')
    cart_item = get_object_or_404(CartItem, id=item_id, cart_id=cart_id)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.info(request, f"تم حذف '{product_name}' من سلة التسوق.")
    return redirect('cart_detail')
