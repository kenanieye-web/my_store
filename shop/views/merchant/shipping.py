from shop.views.merchant.staff_required import staff_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from shop.models.shipping_method import ShippingMethod


@staff_required
def shipping_list(request):
    """صفحة إدارة طرق وشركات الشحن: إضافة، تعديل، حذف، تفعيل/تعطيل"""

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            ShippingMethod.objects.create(
                name=request.POST.get('name', '').strip(),
                company_name=request.POST.get('company_name', '').strip(),
                cost=request.POST.get('cost') or 0,
                estimated_days=request.POST.get('estimated_days') or 1,
                covered_cities=request.POST.get('covered_cities', '').strip(),
                is_active=bool(request.POST.get('is_active')),
            )
            messages.success(request, 'تمت إضافة طريقة الشحن بنجاح')

        elif action == 'edit':
            method = get_object_or_404(ShippingMethod, pk=request.POST.get('method_id'))
            method.name = request.POST.get('name', '').strip()
            method.company_name = request.POST.get('company_name', '').strip()
            method.cost = request.POST.get('cost') or 0
            method.estimated_days = request.POST.get('estimated_days') or 1
            method.covered_cities = request.POST.get('covered_cities', '').strip()
            method.is_active = bool(request.POST.get('is_active'))
            method.save()
            messages.success(request, 'تم تحديث طريقة الشحن بنجاح')

        elif action == 'delete':
            method = get_object_or_404(ShippingMethod, pk=request.POST.get('method_id'))
            method.delete()
            messages.success(request, 'تم حذف طريقة الشحن')

        elif action == 'toggle':
            method = get_object_or_404(ShippingMethod, pk=request.POST.get('method_id'))
            method.is_active = not method.is_active
            method.save()

        return redirect('shipping_settings')

    methods = ShippingMethod.objects.all()
    context = {
        'methods': methods,
        'total_methods': methods.count(),
        'active_methods': methods.filter(is_active=True).count(),
    }
    return render(request, 'admin/shipping_list.html', context)