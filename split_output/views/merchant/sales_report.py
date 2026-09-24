from datetime import timedelta
from django.shortcuts import render
from shop.models import Order, OrderItem
from django.db.models import Q, Sum
from django.utils import timezone

from shop.views.merchant.staff_required import staff_required


@staff_required
def sales_report(request):
    """تقارير المبيعات وتحليل الإيرادات"""
    completed_orders = Order.objects.filter(
        Q(status='delivered') | Q(status='تم التوصيل')
    ).order_by('-created_at')

    period = request.GET.get('period', 'all')
    now = timezone.now()

    if period == 'today':
        completed_orders = completed_orders.filter(created_at__date=now.date())
    elif period == 'week':
        start_of_week = now - timedelta(days=now.weekday())
        completed_orders = completed_orders.filter(created_at__gte=start_of_week)
    elif period == 'month':
        completed_orders = completed_orders.filter(
            created_at__year=now.year, 
            created_at__month=now.month
        )

    all_orders = Order.objects.all()
    total_sales = completed_orders.aggregate(total=Sum('total_price'))['total'] or 0
    
    top_selling_items = OrderItem.objects.filter(
        order__in=completed_orders
    ).values(
        'product__name', 'price'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    context = {
        'completed_orders': completed_orders,
        'total_sales': total_sales,
        'completed_count': completed_orders.count(),
        'total_orders_count': all_orders.count(),
        'top_selling_items': top_selling_items,
        'selected_period': period,
    }
    return render(request, 'shop/sales_report.html', context)
