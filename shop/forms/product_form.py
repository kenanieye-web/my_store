# shop/forms/product_form.py
from django import forms
from shop.models import Product, Category

MAX_GALLERY_IMAGES = 5   # عدد الصور الإضافية (غير الرئيسية)


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        return files.get(name)


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super(MultipleImageField, self).clean(d, initial) for d in data]


class ProductForm(forms.ModelForm):
    gallery = MultipleImageField(
        required=False,
        label="صور إضافية",
        widget=MultipleFileInput(attrs={'class': 'form-control', 'multiple': True, 'accept': 'image/*'}),
    )

    class Meta:
        model = Product
        fields = [
            'name', 'model', 'brand', 'supplier_store_number', 'category', 'description', 'specifications',
            'cost_price', 'stock', 'image', 'is_available',
            'length_cm', 'width_cm', 'height_cm', 'weight_kg',
            'units_per_carton', 'carton_length_cm', 'carton_width_cm', 'carton_height_cm', 'carton_weight_kg',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المنتج'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'موديل المنتج'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الماركة (اختياري) مثل: Dinks'}),
            'supplier_store_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم متجر المورد (اختياري - يظهر لك فقط)'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'وصف المنتج'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'المواصفات الفنية (كل سطر: الخاصية: القيمة)، مثال:\nاللون: أسود\nالطول: 1 متر'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'سعر التكلفة', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'المخزون'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'length_cm': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الطول بالسنتيمتر', 'step': '0.1'}),
            'width_cm': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'العرض بالسنتيمتر', 'step': '0.1'}),
            'height_cm': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'الارتفاع بالسنتيمتر', 'step': '0.1'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 0.050 لوزن 50 غرام (اختياري)', 'step': '0.001'}),
            'units_per_carton': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'عدد القطع داخل الكرتون الواحد'}),
            'carton_length_cm': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'طول الكرتون بالسنتيمتر', 'step': '0.1'}),
            'carton_width_cm': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'عرض الكرتون بالسنتيمتر', 'step': '0.1'}),
            'carton_height_cm': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'ارتفاع الكرتون بالسنتيمتر', 'step': '0.1'}),
            'carton_weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'وزن الكرتون الإجمالي بالكيلوغرام', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # قائمة التصنيفات شجرية بالمسار الكامل: الكترونيات › الأجهزة المنزلية › كاويات
        self.fields['category'].empty_label = "- اختر التصنيف -"
        self.fields['category'].choices = (
            [('', '- اختر التصنيف -')] + [(c.pk, path) for c, _lvl, path in Category.tree()]
        )

    def clean_brand(self):
        brand = (self.cleaned_data.get('brand') or '').strip()
        return brand or None

    def clean_supplier_store_number(self):
        return (self.cleaned_data.get('supplier_store_number') or '').strip()

    def clean_cost_price(self):
        cost_price = self.cleaned_data.get('cost_price')
        if cost_price is not None and cost_price < 0:
            raise forms.ValidationError("سعر التكلفة لا يمكن أن يكون سالباً")
        return cost_price

    def clean_gallery(self):
        files = self.cleaned_data.get('gallery') or []
        if len(files) > MAX_GALLERY_IMAGES:
            raise forms.ValidationError(f"الحد الأقصى {MAX_GALLERY_IMAGES} صور إضافية.")
        return files