import django.db.models


class ShippingMethod(django.db.models.Model):
    name = django.db.models.CharField(max_length=100, verbose_name="اسم طريقة الشحن")
    company_name = django.db.models.CharField(
        max_length=100, blank=True, null=True, verbose_name="اسم شركة التوصيل"
    )
    cost = django.db.models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="رسوم ثابتة إضافية",
        help_text="رسوم تُضاف دائمًا فوق تكلفة الحجم (اتركها 0 إن لم ترغب برسوم ثابتة)"
    )
    price_per_cbm = django.db.models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="سعر الشحن لكل متر مكعب (CBM)"
    )
    min_charge = django.db.models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="الحد الأدنى لتكلفة الشحن"
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
        """قائمة المدن، تقبل الفاصلة العربية (،) واللاتينية (,)"""
        if not self.covered_cities:
            return []
        text = self.covered_cities.replace('،', ',')
        return [city.strip() for city in text.split(',') if city.strip()]

    def covers_city(self, city):
        """إن كانت قائمة المدن فارغة فالطريقة تشمل كل المدن"""
        cities = self.get_cities_list()
        city = (city or '').strip()
        if not cities or not city:
            return True
        return city in cities