from django.shortcuts import render
from shop.models import CustomUser
from django.db.models import Q

from shop.views.merchant.staff_required import staff_required


@staff_required
def staff_user_list(request):
    """عرض طاقم الإدارة"""
    staff_users = CustomUser.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('-date_joined')
    return render(request, 'shop/staff_user_list.html', {'staff_users': staff_users})
