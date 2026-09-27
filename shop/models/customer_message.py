import django.db.models

from shop.models.customer import Customer


class CustomerMessage(django.db.models.Model):
    STATUS_CHOICES = (
        ('new', 'جديد'),
        ('read', 'مقروءة'),
        ('replied', 'تم الرد'),
    )

    customer = django.db.models.ForeignKey(
        Customer, on_delete=django.db.models.SET_NULL, null=True, blank=True,
        related_name='inquiries', verbose_name="العميل (إن كان مسجلاً)"
    )
    name = django.db.models.CharField(max_length=100, verbose_name="الاسم")
    phone = django.db.models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    email = django.db.models.EmailField(blank=True, verbose_name="البريد الإلكتروني")
    subject = django.db.models.CharField(max_length=200, blank=True, verbose_name="الموضوع")
    message = django.db.models.TextField(verbose_name="نص الرسالة")
    status = django.db.models.CharField(max_length=10, choices=STATUS_CHOICES, default='new', verbose_name="الحالة")
    reply_text = django.db.models.TextField(blank=True, verbose_name="نص الرد")
    replied_at = django.db.models.DateTimeField(null=True, blank=True, verbose_name="وقت الرد")
    created_at = django.db.models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الاستلام")

    class Meta:
        verbose_name = "رسالة عميل"
        verbose_name_plural = "رسائل العملاء"
        ordering = ['-created_at']

    def __str__(self):
        return f"رسالة من {self.name} - {self.get_status_display()}"