from django.db import models
from django.utils import timezone

class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'نسبة مئوية (%)'),
        ('fixed', 'مبلغ ثابت'),
    )
    
    code = models.CharField(max_length=50, unique=True, verbose_name="كود الخصم")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage', verbose_name="نوع الخصم")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="قيمة الخصم")
    active = models.BooleanField(default=True, verbose_name="نشط / مفعل")
    valid_from = models.DateTimeField(default=timezone.now, verbose_name="صالح من تاريخ")
    valid_to = models.DateTimeField(verbose_name="صالح حتى تاريخ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "كوبون خصم"
        verbose_name_plural = "الكوبونات والعروض التسويقية"