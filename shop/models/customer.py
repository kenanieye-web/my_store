import django.db.models.signals
from django.conf import settings


class Customer(django.db.models.Model):
    CUSTOMER_TYPE_CHOICES = (
        ('regular', 'عادي'),
        ('wholesale', 'جملة'),
        ('super_wholesale', 'جملة الجملة'),
        ('vip', 'مميز'),
    )

    user = django.db.models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=django.db.models.CASCADE,
        related_name='customer_profile',
        verbose_name="حساب المستخدم"
    )
    phone = django.db.models.CharField(max_length=20, unique=True, blank=False, null=False, verbose_name="الهاتف")
    address = django.db.models.TextField(blank=True, null=True, verbose_name="العنوان")
    city = django.db.models.CharField(max_length=100, default='عدن', verbose_name="المدينة")
    language = django.db.models.CharField(max_length=10, default='العربية', verbose_name="لغة الحساب")
    currency = django.db.models.CharField(max_length=10, default='SAR', verbose_name="العملة المفضلة")
    customer_type = django.db.models.CharField(
        max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='regular', blank=True,
        verbose_name="تصنيف العميل"
    )
    created_at = django.db.models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الانضمام")

    def get_price_tier(self):
        """مستوى السعر: super_wholesale / wholesale / retail (العادي والمميز = تجزئة)"""
        if self.customer_type in ('wholesale', 'super_wholesale'):
            return self.customer_type
        return 'retail'

    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"

    def __str__(self):
        return f"عميل: {self.user.username}"