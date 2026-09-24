"""
URL configuration for my_store project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:
    2. Add a URL to urlpatterns:
    3. Add a class_name:
    4. Add a code:
Class-based views
    1. Add an import:
    2. Add a URL to urlpatterns:
    3. Add a code:
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views  # 1. أضف هذا السطر مع الاستيرادات في الأعلى

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 2. أضف مسارات استعادة كلمة المرور هنا
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='shop/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='shop/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='shop/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='shop/password_reset_complete.html'), name='password_reset_complete'),

    path('', include('shop.urls')),
]

# ربط مجلد الميديا لتخدم الصور أثناء التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 