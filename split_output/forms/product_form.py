from django import forms
from shop.models import Product, Category


class ProductForm(forms.ModelForm):
    # حقل مستقل للمجموعة الرئيسية
    main_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(parent__isnull=True),
        required=True,
        label="المجموعة الرئيسية",
        empty_label="- اختر المجموعة الرئيسية -",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'main-category-select'})
    )
    
    # حقل مستقل للمجموعة الفرعية
    sub_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(parent__isnull=False),
        required=False,
        label="المجموعة الفرعية (اختياري)",
        empty_label="- اختر المجموعة الفرعية (إن وُجدت) -",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'sub-category-select'})
    )

    class Meta:
        model = Product
        fields = ['name', 'model', 'description', 'price', 'stock', 'image', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المنتج'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'موديل المنتج'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'وصف المنتج'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'السعر'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'المخزون'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # في حالة التعديل، جلب القيم الحالية وتعبئتها في الحقلين
        if self.instance and self.instance.pk and self.instance.category:
            if self.instance.category.parent:
                self.fields['main_category'].initial = self.instance.category.parent
                self.fields['sub_category'].initial = self.instance.category
            else:
                self.fields['main_category'].initial = self.instance.category

    def save(self, commit=True):
        product = super().save(commit=False)
        sub_cat = self.cleaned_data.get('sub_category')
        main_cat = self.cleaned_data.get('main_category')
        
        # إذا اختار المستخدم مجموعة فرعية، يتم اعتمادها كفئة للمنتج، وإلا يتم اعتماد الرئيسية
        if sub_cat:
            product.category = sub_cat
        else:
            product.category = main_cat
            
        if commit:
            product.save()
        return product
