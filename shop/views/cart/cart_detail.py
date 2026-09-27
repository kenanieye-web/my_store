from django.shortcuts import render
from shop.models import Cart, ShippingMethod
from shop.utils.shipping import calculate_shipping_cost


def cart_detail(request):
    """عرض محتويات سلة التسوق مع خيارات الشحن"""
    cart_id = request.session.get('cart_id')
    cart = None
    shipping_options = []

    if cart_id:
        cart = Cart.objects.filter(id=cart_id).prefetch_related('items__product').first()

    if cart and cart.items.exists():
        items = [(item.product, item.quantity) for item in cart.items.all()]

        for method in ShippingMethod.objects.filter(is_active=True):
            result = calculate_shipping_cost(items, method)
            shipping_options.append({
                'method_id': method.id,
                'method_name': method.name,
                'company_name': method.company_name,
                'cost': result['cost'],
                'delivery_days': result['delivery_days'],
                'covered_cities': method.get_cities_list(),
            })

    selected_shipping_id = request.session.get('selected_shipping_id')
    selected_shipping = next(
        (opt for opt in shipping_options if opt['method_id'] == selected_shipping_id),
        shipping_options[0] if shipping_options else None
    )

    context = {
        'cart': cart,
        'shipping_options': shipping_options,
        'selected_shipping': selected_shipping,
    }
    return render(request, 'shop/cart/cart_detail.html', context)