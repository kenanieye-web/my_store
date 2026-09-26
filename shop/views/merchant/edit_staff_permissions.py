from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from .staff_required import staff_required

User = get_user_model()

@staff_required
def edit_staff_permissions(request, user_id):
    staff_user = get_object_or_404(User, pk=user_id, is_staff=True)
    # فقط صلاحيات موديلاتك الخاصة (shop) وليس كل صلاحيات Django
    all_permissions = Permission.objects.filter(content_type__app_label='shop').select_related('content_type')

    if request.method == 'POST':
        selected_ids = request.POST.getlist('permissions')
        staff_user.user_permissions.set(selected_ids)
        return redirect('staff_user_list')

    current_permissions_ids = list(staff_user.user_permissions.values_list('id', flat=True))

    return render(request, 'shop/merchant/edit_staff_permissions.html', {
        'staff_user': staff_user,
        'all_permissions': all_permissions,
        'current_permissions_ids': current_permissions_ids,
    })