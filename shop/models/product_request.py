import django.db.models

from shop.models.customer import Customer


class ProductRequest(django.db.models.Model):
    STATUS_CHOICES = (
        ('new', 'جديد'),
        ('reviewing', 'قيد المراجعة'),
        ('available', 'تم التوفير'),
        ('rejected', 'غير متاح'),
    )

    customer = django.db.models.ForeignKey(
        Customer, on_delete=django.db.models.SET_NULL, null=True, blank=True,
        related_name='product_requests', verbose_name="العميل (إن كان مسجلاً)"
    )
    full_name = django.db.models.CharField(max_length=100, verbose_name="اسم مقدم الطلب")
    phone = django.db.models.CharField(max_length=20, verbose_name="رقم الهاتف")
    product_name = django.db.models.CharField(max_length=200, verbose_name="اسم المنتج المطلوب")
    specifications = django.db.models.TextField(blank=True, verbose_name="مواصفات المنتج")
    quantity = django.db.models.PositiveIntegerField(default=1, verbose_name="الكمية المطلوبة")
    approximate_price = django.db.models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="السعر التقريبي (إن وجد)"
    )
    video_url = django.db.models.URLField(
        blank=True, null=True, verbose_name="رابط فيديو للمنتج (اختياري)",
        help_text="رابط يوتيوب أو تيك توك أو أي منصة أخرى يوضح المنتج المطلوب"
    )
    notes = django.db.models.TextField(blank=True, verbose_name="ملاحظات إضافية")
    status = django.db.models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="الحالة")
    created_at = django.db.models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")

    class Meta:
        verbose_name = "طلب منتج غير متوفر"
        verbose_name_plural = "طلبات المنتجات غير المتوفرة"
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب: {self.product_name} - {self.full_name}"


class ProductRequestImage(django.db.models.Model):
    request = django.db.models.ForeignKey(
        ProductRequest, on_delete=django.db.models.CASCADE, related_name='images',
        verbose_name="الطلب"
    )
    image = django.db.models.ImageField(upload_to='product_requests/', verbose_name="صورة")

    def __str__(self):
        return f"صورة لطلب #{self.request_id}"