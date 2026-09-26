import django.db.models


class PaymentMethod(django.db.models.Model):
    PAYMENT_TYPE_CHOICES = (
        ('cash', 'الدفع عند الاستلام'),
        ('bank_transfer', 'تحويل بنكي'),
        ('mobile_wallet', 'محفظة إلكترونية'),
        ('card', 'بطاقة ائتمان'),
        ('other', 'أخرى'),
    )

    name = django.db.models.CharField(max_length=100, verbose_name="اسم طريقة الدفع")
    payment_type = django.db.models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='cash',
        verbose_name="نوع طريقة الدفع",
    )
    instructions = django.db.models.TextField(
        blank=True,
        verbose_name="تعليمات الدفع (تظهر للعميل)",
        help_text="مثال: رقم الحساب البنكي، اسم المستفيد، أو أي تفاصيل يحتاجها العميل",
    )
    is_active = django.db.models.BooleanField(default=True, verbose_name="مفعّلة")
    created_at = django.db.models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    class Meta:
        verbose_name = "طريقة دفع"
        verbose_name_plural = "طرق الدفع"
        ordering = ['-is_active', 'name']

    def __str__(self):
        return self.name