from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render

from shop.models import PricingSettings
from shop.views.merchant.staff_required import staff_required


class PricingSettingsForm(forms.ModelForm):
    class Meta:
        model = PricingSettings
        fields = [
            'retail_margin_percent',
            'wholesale_margin_percent',
            'super_wholesale_margin_percent',
        ]
        widgets = {
            name: forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '1000',
            })
            for name in fields
        }

    def clean(self):
        cleaned = super().clean()
        for name in self.Meta.fields:
            value = cleaned.get(name)
            if value is not None and not (0 <= value <= 1000):
                self.add_error(name, "النسبة يجب أن تكون بين 0 و1000")
        return cleaned


@staff_required
def pricing_settings(request):
    """تعديل نسب الربح (تجزئة / جملة / جملة الجملة) من لوحة التاجر"""
    instance = PricingSettings.get_solo()
    if request.method == 'POST':
        form = PricingSettingsForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "تم حفظ نسب التسعير، وتسري الآن على كل المنتجات.")
            return redirect('pricing_settings')
    else:
        form = PricingSettingsForm(instance=instance)
    return render(request, 'shop/merchant/pricing_settings.html', {
        'form': form,
        'settings_obj': instance,
    })