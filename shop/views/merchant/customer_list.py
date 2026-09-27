from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from shop.models import Customer
from shop.views.merchant.staff_required import staff_required

User = get_user_model()


@staff_required
def customer_list(request):
    """عرض وإدارة قائمة العملاء: بحث، فلترة، إحصائيات، إضافة عميل، وتصنيفه"""

    if request.method == 'POST':
        action = request.POST.get('action', 'add')

        if action == 'add':
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            city = request.POST.get('city', '').strip() or 'عدن'
            address = request.POST.get('address', '').strip()

            if not full_name or not phone:
                messages.error(request, 'الاسم ورقم الهاتف مطلوبان')
            elif Customer.objects.filter(phone=phone).exists():
                messages.error(request, 'رقم الهاتف مسجل مسبقًا لعميل آخر')
            else:
                user = User.objects.create_user(username=phone, first_name=full_name)
                user.set_unusable_password()
                user.save()
                Customer.objects.create(user=user, phone=phone, city=city, address=address)
                messages.success(request, 'تمت إضافة العميل بنجاح')

        elif action == 'edit_type':
            customer = get_object_or_404(Customer, pk=request.POST.get('customer_id'))
            new_type = request.POST.get('customer_type')
            if new_type in dict(Customer.CUSTOMER_TYPE_CHOICES):
                customer.customer_type = new_type
                customer.save()
                messages.success(request, 'تم تحديث تصنيف العميل')

        return redirect('customer_list')

    customers = (
        Customer.objects
        .select_related('user')
        .annotate(orders_count=Count('order'))
        .order_by('-id')
    )

    search_query = request.GET.get('q', '').strip()
    if search_query:
        customers = customers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    city_filter = request.GET.get('city', '').strip()
    if city_filter:
        customers = customers.filter(city=city_filter)

    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        customers = customers.filter(customer_type=type_filter)

    total_customers = Customer.objects.count()
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_this_month = Customer.objects.filter(created_at__gte=thirty_days_ago).count()
    returning_customers = Customer.objects.annotate(orders_count=Count('order')).filter(orders_count__gt=1).count()
    all_cities = Customer.objects.values_list('city', flat=True).distinct().order_by('city')

    context = {
        'customers': customers,
        'total_customers': total_customers,
        'new_this_month': new_this_month,
        'returning_customers': returning_customers,
        'all_cities': all_cities,
        'search_query': search_query,
        'city_filter': city_filter,
        'type_filter': type_filter,
        'customer_type_choices': Customer.CUSTOMER_TYPE_CHOICES,
    }
    return render(request, 'shop/merchant/customer_list.html', context)