from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout


def logout_user(request):
    """تسجيل الخروج"""
    logout(request)
    messages.info(request, "تم تسجيل الخروج بنجاح.")
    return redirect('home')
