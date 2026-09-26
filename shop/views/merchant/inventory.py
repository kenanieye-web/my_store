from shop.views.merchant.staff_required import staff_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from shop.models.product import Product

LOW_STOCK_THRESHOLD = 5


@staff_required
def inventory_list(request):
    """صفحة إدارة المخزون: عرض الكميات، تعديلها، وتنبيهات نفاد المخزون"""

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_stock = request.POST.get('stock')
        product = get_object_or_404(Product, pk=product_id)
        try:
            new_stock = int(new_stock)
            if new_stock < 0:
                raise ValueError
            product.stock = new_stock
            # إذا أصبح المخزون صفراً، نجعل المنتج غير متاح تلقائياً
            product.is_available = new_stock > 0
            product.save()
            messages.success(request, f'تم تحديث مخزون "{product.name}" إلى {new_stock} قطعة')
        except (ValueError, TypeError):
            messages.error(request, 'الكمية المدخلة غير صحيحة، يجب أن تكون رقماً صحيحاً موجباً')
        return redirect('inventory_list')

    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')

    products = Product.objects.all().order_by('stock')

    if search_query:
        products = products.filter(name__icontains=search_query)

    if status_filter == 'low':
        products = products.filter(stock__gt=0, stock__lte=LOW_STOCK_THRESHOLD)
    elif status_filter == 'out':
        products = products.filter(stock__lte=0)

    context = {
        'products': products,
        'status_filter': status_filter,
        'search_query': search_query,
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
        'total_products': Product.objects.count(),
        'low_stock_count': Product.objects.filter(
            stock__gt=0, stock__lte=LOW_STOCK_THRESHOLD
        ).count(),
        'out_of_stock_count': Product.objects.filter(stock__lte=0).count(),
    }
    return render(request, 'admin/inventory_list.html', context)