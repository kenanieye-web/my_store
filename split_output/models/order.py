import django.db.models.signals
from django.conf import settings

from shop.models.customer import Customer


class Order(django.db.models.Model):
    STATUS_CHOICES = (
        ('new', 'جديد'),
        ('shipping', 'جاري الشحن'),
        ('delivered', 'تم التوصيل'),
        ('canceled', 'ملغى'),
    )

    user = django.db.models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=django.db.models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="المستخدم"
    )
    customer = django.db.models.ForeignKey(
        Customer, 
        on_delete=django.db.models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="العميل"
    )
    full_name = django.db.models.CharField(max_length=100, verbose_name="اسم العميل")
    city = django.db.models.CharField(max_length=50, verbose_name="المدينة")
    address = django.db.models.TextField(verbose_name="العنوان")
    phone = django.db.models.CharField(max_length=20, verbose_name="رقم الهاتف")
    total_price = django.db.models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر الكلي")
    status = django.db.models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='new', 
        verbose_name="حالة الطلب"
    )
    created_at = django.db.models.DateTimeField(auto_now_add=True, verbose_name="وقت وتاريخ الطلب")

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب #{self.id} - {self.full_name}"
