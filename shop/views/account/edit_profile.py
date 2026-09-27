from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from shop.forms.edit_profile_form import EditProfileForm


@login_required(login_url='login')
def edit_profile(request):
    """السماح للعميل بتعديل بياناته الشخصية: الاسم، البريد الإلكتروني، الهاتف، والعنوان"""
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث بياناتك الشخصية بنجاح.")
            return redirect('customer_profile')
    else:
        form = EditProfileForm(instance=request.user)

    return render(request, 'shop/accounts/edit_profile.html', {'form': form})