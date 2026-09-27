from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from shop.models import ProductRequest
from shop.views.merchant.staff_required import staff_required


@staff_required
def product_requests_list(request):
    """عرض وإدارة طلبات المنتجات غير المتوفرة من العملاء"""
    if request.method == 'POST':
        req = get_object_or_404(ProductRequest, pk=request.POST.get('request_id'))
        new_status = request.POST.get('status')
        if new_status in dict(ProductRequest.STATUS_CHOICES):
            req.status = new_status
            req.save()
            messages.success(request, 'تم تحديث حالة الطلب')
        return redirect('product_requests_list')

    status_filter = request.GET.get('status', '')
    requests_qs = ProductRequest.objects.prefetch_related('images').all()
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    new_count = ProductRequest.objects.filter(status='new').count()

    context = {
        'product_requests': requests_qs,
        'status_filter': status_filter,
        'new_count': new_count,
    }
    return render(request, 'shop/merchant/product_requests_list.html', context)