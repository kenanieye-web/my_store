import django.db.models.signals
from decimal import Decimal

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

    # ===== أبعاد العلبة الفردية لحساب الشحن (CBM) =====
    length_cm = django.db.models.DecimalField(
        max_digits=6, decimal_places=1, default=0, blank=True,
        verbose_name="الطول (سم)"
    )
    width_cm = django.db.models.DecimalField(
        max_digits=6, decimal_places=1, default=0, blank=True,
        verbose_name="العرض (سم)"
    )
    height_cm = django.db.models.DecimalField(
        max_digits=6, decimal_places=1, default=0, blank=True,
        verbose_name="الارتفاع (سم)"
    )
    weight_kg = django.db.models.DecimalField(
        max_digits=6, decimal_places=3, default=0, blank=True,
        verbose_name="الوزن الفعلي (كغم)",
        help_text="اختياري - لوزن الأشياء الخفيفة استخدم كسورًا عشرية، مثال: 0.050 = 50 غرام"
    )

    # ===== بيانات الكرتون الرئيسي (Master Carton) لحساب شحن أدق بالجملة =====
    units_per_carton = django.db.models.PositiveIntegerField(
        default=1, blank=True,
        verbose_name="عدد القطع في الكرتون الواحد"
    )
    carton_length_cm = django.db.models.DecimalField(
        max_digits=6, decimal_places=1, default=0, blank=True,
        verbose_name="طول الكرتون (سم)"
    )
    carton_width_cm = django.db.models.DecimalField(
        max_digits=6, decimal_places=1, default=0, blank=True,
        verbose_name="عرض الكرتون (سم)"
    )
    carton_height_cm = django.db.models.DecimalField(
        max_digits=6, decimal_places=1, default=0, blank=True,
        verbose_name="ارتفاع الكرتون (سم)"
    )
    carton_weight_kg = django.db.models.DecimalField(
        max_digits=6, decimal_places=2, default=0, blank=True,
        verbose_name="وزن الكرتون الفعلي (كغم)",
        help_text="اختياري - الوزن الكلي للكرتون بكل قطعه"
    )

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

    def get_carton_cbm(self):
        """الحجم الكلي بالمتر المكعب للكرتون الواحد بكل قطعه"""
        if not (self.carton_length_cm and self.carton_width_cm and self.carton_height_cm):
            return Decimal("0")
        cbm = (
            Decimal(self.carton_length_cm)
            * Decimal(self.carton_width_cm)
            * Decimal(self.carton_height_cm)
        ) / Decimal("1000000")
        return cbm.quantize(Decimal("0.000001"))

    def get_cbm(self):
        """
        الحجم بالمتر المكعب لقطعة واحدة.
        إذا توفرت بيانات الكرتون (أدق لأنها تشمل الحشو الفعلي)، يُحسب حجم القطعة
        بقسمة حجم الكرتون على عدد القطع بداخله، وإلا يُستخدم حجم العلبة الفردية.
        """
        carton_cbm = self.get_carton_cbm()
        if carton_cbm > 0 and self.units_per_carton:
            per_unit_cbm = carton_cbm / Decimal(self.units_per_carton)
            return per_unit_cbm.quantize(Decimal("0.000001"))

        if not (self.length_cm and self.width_cm and self.height_cm):
            return Decimal("0")
        cbm = (
            Decimal(self.length_cm)
            * Decimal(self.width_cm)
            * Decimal(self.height_cm)
        ) / Decimal("1000000")
        return cbm.quantize(Decimal("0.000001"))