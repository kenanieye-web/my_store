from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from shop.models import CustomerMessage
from shop.views.merchant.staff_required import staff_required


@staff_required
def customer_messages_list(request):
    """عرض رسائل واستفسارات العملاء والرد عليها"""
    if request.method == 'POST':
        action = request.POST.get('action')
        msg = get_object_or_404(CustomerMessage, pk=request.POST.get('message_id'))

        if action == 'reply':
            reply_text = request.POST.get('reply_text', '').strip()
            if reply_text:
                msg.reply_text = reply_text
                msg.status = 'replied'
                msg.replied_at = timezone.now()
                msg.save()
                messages.success(request, 'تم حفظ الرد بنجاح')
        elif action == 'mark_read':
            msg.status = 'read'
            msg.save()

        return redirect('customer_messages_list')

    status_filter = request.GET.get('status', '')
    customer_messages = CustomerMessage.objects.select_related('customer').all()
    if status_filter:
        customer_messages = customer_messages.filter(status=status_filter)

    new_count = CustomerMessage.objects.filter(status='new').count()

    context = {
        'customer_messages': customer_messages,
        'status_filter': status_filter,
        'new_count': new_count,
    }
    return render(request, 'shop/merchant/customer_messages_list.html', context)