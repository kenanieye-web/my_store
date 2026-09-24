from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from shop.forms import CustomerLoginForm


def login_user(request):
    """تسجيل الدخول للعميل عبر البريد الإلكتروني"""
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "مرحباً بك مجدداً في المتجر!")
                return redirect('customer_profile')
        else:
            messages.error(request, "البريد الإلكتروني أو كلمة المرور غير صحيحة.")
    else:
        form = CustomerLoginForm()
        
    return render(request, 'shop/login.html', {'form': form})
