import django.db.models


class ShippingMethod(django.db.models.Model):
    name = django.db.models.CharField(max_length=100, verbose_name="اسم طريقة الشحن")
    company_name = django.db.models.CharField(
        max_length=100, blank=True, null=True, verbose_name="اسم شركة التوصيل"
    )
    cost = django.db.models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="تكلفة الشحن"
    )
    estimated_days = django.db.models.PositiveIntegerField(
        default=1, verbose_name="مدة التوصيل المتوقعة (أيام)"
    )
    covered_cities = django.db.models.TextField(
        blank=True,
        verbose_name="المدن المشمولة",
        help_text="افصل بين أسماء المدن بفاصلة، مثال: صنعاء، عدن، تعز",
    )
    is_active = django.db.models.BooleanField(default=True, verbose_name="مفعّلة")
    created_at = django.db.models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    class Meta:
        verbose_name = "طريقة شحن"
        verbose_name_plural = "طرق الشحن"
        ordering = ['cost']

    def __str__(self):
        return self.name

    def get_cities_list(self):
        """إرجاع قائمة بأسماء المدن بعد تقسيم النص المفصول بفواصل"""
        if not self.covered_cities:
            return []
        return [city.strip() for city in self.covered_cities.split(',') if city.strip()]