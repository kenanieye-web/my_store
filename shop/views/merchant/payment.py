from shop.views.merchant.staff_required import staff_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from shop.models.payment_method import PaymentMethod


@staff_required
def payment_list(request):
    """صفحة إدارة طرق الدفع: إضافة، تعديل، حذف، تفعيل/تعطيل"""

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            PaymentMethod.objects.create(
                name=request.POST.get('name', '').strip(),
                payment_type=request.POST.get('payment_type', 'cash'),
                instructions=request.POST.get('instructions', '').strip(),
                is_active=bool(request.POST.get('is_active')),
            )
            messages.success(request, 'تمت إضافة طريقة الدفع بنجاح')

        elif action == 'edit':
            method = get_object_or_404(PaymentMethod, pk=request.POST.get('method_id'))
            method.name = request.POST.get('name', '').strip()
            method.payment_type = request.POST.get('payment_type', 'cash')
            method.instructions = request.POST.get('instructions', '').strip()
            method.is_active = bool(request.POST.get('is_active'))
            method.save()
            messages.success(request, 'تم تحديث طريقة الدفع بنجاح')

        elif action == 'delete':
            method = get_object_or_404(PaymentMethod, pk=request.POST.get('method_id'))
            method.delete()
            messages.success(request, 'تم حذف طريقة الدفع')

        elif action == 'toggle':
            method = get_object_or_404(PaymentMethod, pk=request.POST.get('method_id'))
            method.is_active = not method.is_active
            method.save()

        return redirect('payment_settings')

    methods = PaymentMethod.objects.all()
    context = {
        'methods': methods,
        'payment_type_choices': PaymentMethod.PAYMENT_TYPE_CHOICES,
        'total_methods': methods.count(),
        'active_methods': methods.filter(is_active=True).count(),
    }
    return render(request, 'admin/payment_list.html', context)