from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from shop.models import Order

from shop.views.merchant.staff_required import staff_required


@staff_required
def order_detail(request, pk):
    """تفاصيل الطلب وتحديث حالته"""
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
            messages.success(request, f"تم تحديث حالة الطلب #{order.id} بنجاح.")
            return redirect('order_detail', pk=order.id)

    return render(request, 'shop/order_detail.html', {'order': order})
