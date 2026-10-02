from decimal import Decimal

from django.db import models


class PricingSettings(models.Model):
    """إعدادات التسعير العامة (سجل واحد فقط) - تُعدَّل من لوحة التحكم."""

    TIER_RETAIL = 'retail'
    TIER_WHOLESALE = 'wholesale'
    TIER_SUPER_WHOLESALE = 'super_wholesale'

    retail_margin_percent = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("30.00"),
        verbose_name="نسبة الربح - تجزئة (%)"
    )
    wholesale_margin_percent = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("15.00"),
        verbose_name="نسبة الربح - جملة (%)"
    )
    super_wholesale_margin_percent = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("5.00"),
        verbose_name="نسبة الربح - جملة الجملة (%)"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        verbose_name = "إعدادات التسعير"
        verbose_name_plural = "إعدادات التسعير"

    def __str__(self):
        return "إعدادات التسعير"

    def save(self, *args, **kwargs):
        self.pk = 1  # سجل واحد فقط
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # منع الحذف

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def get_margin(self, tier):
        if tier == self.TIER_SUPER_WHOLESALE:
            return self.super_wholesale_margin_percent
        if tier == self.TIER_WHOLESALE:
            return self.wholesale_margin_percent
        return self.retail_margin_percent