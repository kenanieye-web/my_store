from django import forms
from django.contrib.auth.forms import UserCreationForm
from shop.models import CustomUser
from shop.models import Customer


class CustomerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="البريد الإلكتروني")
    phone = forms.CharField(max_length=9, required=True, label="رقم الهاتف")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), required=False, label="العنوان")
    city = forms.CharField(max_length=100, initial='عدن', required=True, label="المدينة", widget=forms.TextInput(attrs={'class': 'form-control'}))
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # التحقق من أن رقم الهاتف مكون من 9 أرقام صحيحة
        if not phone or not phone.isdigit() or len(phone) != 9:
            raise forms.ValidationError("عذراً، يجب أن يكون رقم الهاتف مكوناً من 9 أرقام صحيحة.")
        # التحقق من عدم تكرار رقم الهاتف مع عميل سابق
        if Customer.objects.filter(phone=phone).exists():
            raise forms.ValidationError("عذراً، رقم الهاتف هذا مسجل مسبقاً بحساب عميل آخر.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # التحقق من عدم تكرار البريد الإلكتروني مع حساب سابق
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("عذراً، البريد الإلكتروني مسجل مسبقاً بحساب آخر.")
        return email
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'username', 'phone', 'address', 'city')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المستخدم'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # تحديث أو إنشـاء ملف العميل المرتبط تلقائياً
            customer, created = Customer.objects.get_or_create(user=user)
            customer.phone = self.cleaned_data.get('phone')
            customer.address = self.cleaned_data.get('address')
            customer.city = self.cleaned_data.get('city')
            customer.save()
        return user
