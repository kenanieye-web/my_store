from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomerLoginForm(AuthenticationForm):
    username = forms.EmailField(label="البريد الإلكتروني", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'كلمة المرور'}))
