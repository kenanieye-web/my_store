from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from .staff_required import staff_required

User = get_user_model()

@staff_required
def add_staff(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود بالفعل')
            return redirect('add_staff')

        new_staff = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=False
        )
        messages.success(request, 'تم إضافة الموظف بنجاح، يمكنك الآن تحديد صلاحياته')
        return redirect('edit_staff_permissions', user_id=new_staff.id)

    return render(request, 'shop/merchant/add_staff.html')