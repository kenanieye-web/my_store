from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from shop.models import PricingSettings


@admin.register(PricingSettings)
class PricingSettingsAdmin(admin.ModelAdmin):
    """صفحة واحدة لتعديل نسب الربح: سعر البيع = التكلفة + النسبة."""

    fieldsets = (
        ("نسب الربح على سعر التكلفة", {
            'description': (
                "سعر البيع = سعر التكلفة + (سعر التكلفة × النسبة ÷ 100). "
                "التعديل يسري فوراً على كل المنتجات والطلبات الجديدة، "
                "ولا يغيّر أسعار الطلبات السابقة."
            ),
            'fields': (
                'retail_margin_percent',
                'wholesale_margin_percent',
                'super_wholesale_margin_percent',
            ),
        }),
        (None, {'fields': ('updated_at',)}),
    )
    readonly_fields = ['updated_at']

    def has_add_permission(self, request):
        return not PricingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # سجل واحد فقط: نفتح صفحة التعديل مباشرة
        obj = PricingSettings.get_solo()
        return redirect(reverse('admin:shop_pricingsettings_change', args=[obj.pk]))
    