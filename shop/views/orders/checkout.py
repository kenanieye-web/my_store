from django.shortcuts import render, redirect
from django.contrib import messages
from shop.models import Cart, Order, OrderItem
from django.db import transaction


@transaction.atomic
def checkout(request):
    """صفحة إتمام الطلب الشراء"""
    cart_id = request.session.get('cart_id')
    cart = Cart.objects.filter(id=cart_id).prefetch_related('items__product').first() if cart_id else None

    if not cart or not cart.items.exists():
        messages.warning(request, "سلة التسوق فارغة!")
        return redirect('product_list')

    total_price = sum((item.get_total_price() for item in cart.items.all()), 0)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        city = request.POST.get('city', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not all([full_name, city, address, phone]):
            messages.error(request, "يرجى ملء جميع حقول الشحن المطلوبة.")
            return render(request, 'shop/checkout.html', {'cart': cart, 'total_price': total_price})

        customer_profile = getattr(request.user, 'customer_profile', None) if request.user.is_authenticated else None

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer=customer_profile,
            full_name=full_name,
            city=city,
            address=address,
            phone=phone,
            total_price=total_price
        )

        order_items = [
            OrderItem(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
            for item in cart.items.all()
        ]
        OrderItem.objects.bulk_create(order_items)

        cart.delete()
        if 'cart_id' in request.session:
            del request.session['cart_id']

        messages.success(request, f"تم إتمام طلبك بنجاح! رقم الطلب #{order.id}")
        return redirect('order_success', order_id=order.id)

    return render(request, 'shop/checkout.html', {'cart': cart, 'total_price': total_price})
