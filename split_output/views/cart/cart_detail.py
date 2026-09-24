from django.shortcuts import render
from shop.models import Cart


def cart_detail(request):
    """عرض محتويات سلة التسوق"""
    cart_id = request.session.get('cart_id')
    cart = None
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).prefetch_related('items__product').first()
    return render(request, 'shop/cart_detail.html', {'cart': cart})
