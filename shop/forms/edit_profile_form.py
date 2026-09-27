from django import forms
from shop.models import CustomUser, Customer


class EditProfileForm(forms.ModelForm):
    """تعديل البيانات الشخصية للعميل: الاسم والبريد من CustomUser، والهاتف والعنوان والمدينة من Customer"""

    phone = forms.CharField(
        max_length=9, required=True, label="رقم الهاتف",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف (9 أرقام)'})
    )
    address = forms.CharField(
        required=False, label="العنوان",
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'العنوان بالتفصيل...'})
    )
    city = forms.CharField(
        max_length=100, required=True, label="المدينة",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدينة'})
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الأول'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم العائلة'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # جلب بيانات Customer المرتبطة وتعبئتها كقيم ابتدائية بالحقول الإضافية
        if self.instance and self.instance.pk:
            customer, _ = Customer.objects.get_or_create(user=self.instance)
            self.fields['phone'].initial = customer.phone
            self.fields['address'].initial = customer.address
            self.fields['city'].initial = customer.city

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # السماح للمستخدم بالاحتفاظ ببريده الحالي، مع منع التكرار مع مستخدم آخر
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("هذا البريد الإلكتروني مستخدم بالفعل من قبل حساب آخر.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone or not phone.isdigit() or len(phone) != 9:
            raise forms.ValidationError("عذراً، يجب أن يكون رقم الهاتف مكوناً من 9 أرقام صحيحة.")
        if Customer.objects.filter(phone=phone).exclude(user=self.instance).exists():
            raise forms.ValidationError("عذراً، رقم الهاتف هذا مسجل مسبقاً بحساب عميل آخر.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=commit)
        customer, _ = Customer.objects.get_or_create(user=user)
        customer.phone = self.cleaned_data.get('phone')
        customer.address = self.cleaned_data.get('address')
        customer.city = self.cleaned_data.get('city')
        if commit:
            customer.save()
        return user