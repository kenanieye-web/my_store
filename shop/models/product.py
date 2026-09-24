import django.db.models.signals

from shop.models.category import Category


class Product(django.db.models.Model):
    name = django.db.models.CharField(max_length=200, verbose_name="اسم المنتج")
    model = django.db.models.CharField(max_length=100, blank=True, null=True, verbose_name="الموديل")
    category = django.db.models.ForeignKey(
        Category, 
        on_delete=django.db.models.CASCADE, 
        related_name='products',
        verbose_name="التصنيف"
    )
    description = django.db.models.TextField(blank=True, verbose_name="الوصف")
    specifications = django.db.models.TextField(blank=True, null=True, verbose_name="المواصفات الفنية")
    price = django.db.models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    image = django.db.models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="الصورة الرئيسية")
    video = django.db.models.FileField(upload_to='products/videos/', blank=True, null=True, verbose_name="فيديو المنتج", help_text="يمكنك رفع فيديو للمنتج (MP4)")
    is_available = django.db.models.BooleanField(default=True, verbose_name="متاح للبيع")
    stock = django.db.models.IntegerField(default=0, verbose_name="المخزون")
    colors = django.db.models.CharField(max_length=200, blank=True, null=True, verbose_name="الألوان المتاحة")
    rating = django.db.models.FloatField(default=5.0, verbose_name="تقييم المنتج")
    reviews_count = django.db.models.IntegerField(default=0, verbose_name="عدد التقييمات")
    created_at = django.db.models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_main_category(self):
        """إرجاع التصنيف الرئيسي للمنتج سواء كان مرتبطاً بتصنيف فرعي أو رئيسي مباشرة"""
        if self.category and self.category.parent:
            return self.category.parent
        return self.category
