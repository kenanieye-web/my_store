from django import forms
from .models import Product, Category


# تخصيص حقل الاختيار ليظهر "المجموعة الرئيسية -> المجموعة الفرعية"
class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.parent:
            return f"{obj.parent.name} ⬅ {obj.name}"
        return f"[مجموعة رئيسية] {obj.name}"


class ProductForm(forms.ModelForm):
    # إعادة تعريف حقل التصنيف ليستخدم التنسيق الشجري
    category = CategoryChoiceField(
        queryset=Category.objects.all().select_related('parent'),
        label="التصنيف",
        empty_label="- اختر التصنيف (رئيسي / فرعي) -",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Product
        fields = ['name', 'model', 'category', 'description', 'price', 'stock', 'image', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المنتج'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'موديل المنتج'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'وصف المنتج'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'السعر'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'المخزون'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }