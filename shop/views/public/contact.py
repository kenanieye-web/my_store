from django.shortcuts import render, redirect
from django.contrib import messages

from shop.models import CustomerMessage


def contact_us(request):
    """صفحة تواصل معنا: استقبال استفسارات العملاء"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        if not name or not message_text:
            messages.error(request, 'الرجاء إدخال الاسم ونص الرسالة')
        else:
            customer = None
            if request.user.is_authenticated:
                customer = getattr(request.user, 'customer_profile', None)

            CustomerMessage.objects.create(
                customer=customer, name=name, phone=phone,
                email=email, subject=subject, message=message_text,
            )
            messages.success(request, 'تم إرسال رسالتك بنجاح، سنتواصل معك قريبًا')
            return redirect('contact_us')

    return render(request, 'shop/public/contact.html')