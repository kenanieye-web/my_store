from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from shop.forms import CustomerSignUpForm


def register_user(request):
    """تسجيل حساب عميل جديد باستخدام النماذج المخصصة"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':      
        form = CustomerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "تم إنشاء الحساب وتسجيل الدخول بنجاح!")
            return redirect('customer_profile')
    else:
        form = CustomerSignUpForm()
    
    return render(request, 'shop/register.html', {'form': form})
