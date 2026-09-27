from django.shortcuts import redirect
from django.contrib import messages


def select_shipping_method(request):
    """حفظ طريقة الشحن التي اختارها العميل في السلة"""
    if request.method != 'POST':
        return redirect('cart_detail')

    method_id = request.POST.get('shipping_method_id')
    try:
        request.session['selected_shipping_id'] = int(method_id)
    except (ValueError, TypeError):
        messages.error(request, "الرجاء اختيار طريقة شحن صحيحة.")

    return redirect('cart_detail')