import django.db.models.signals
from decimal import Decimal
from shop.models.category import Category
from shop.models.pricing_settings import PricingSettings
class Product(django.db.models.Model):
    name = django.db.models.CharField(max_length=200, verbose_name="اسم المنتج")
    model = django.db.models.CharField(max_length=100, blank=True, null=True, verbose_name="الموديل")
    brand = django.db.models.CharField(max_length=100, blank=True, null=True, verbose_name="الماركة")
    # رقم متجر المورد (داخلي للتاجر فقط - لا يُعرض للعملاء ولا في الـ API)
    supplier_store_number = django.db.models.CharField(
        max_length=100, blank=True, default="",
        verbose_name="رقم متجر المورد",
        help_text="اختياري - يظهر لك فقط في تفاصيل الطلب والطباعة ولا يراه العميل"
    )
    category = django.db.models.ForeignKey(
        Category, 
        on_delete=django.db.models.CASCADE, 
        related_name='products',
        verbose_name="التصنيف"
    )
    description = django.db.models.TextField(blank=True, verbose_name="الوصف")
    specifications = django.db.models.TextField(blank=True, null=True, verbose_name="المواصفات الفنية")
    cost_price = django.db.models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر التكلفة")
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
        """التصنيف الجذر للمنتج مهما كان عمق التصنيف"""
        node = self.category
        while node is not None and node.parent_id:
            node = node.parent
        return node
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

    # ===== التسعير: سعر البيع = التكلفة + نسبة الربح حسب مستوى العميل =====
    def get_price(self, tier='retail', pricing=None):
        """سعر البيع لمستوى معيّن: retail / wholesale / super_wholesale
        pricing: كائن PricingSettings اختياري لتفادي استعلام لكل منتج في القوائم"""
        pricing = pricing or PricingSettings.get_solo()
        margin = pricing.get_margin(tier)
        cost = Decimal(self.cost_price or 0)
        price = cost + (cost * Decimal(margin) / Decimal("100"))
        return price.quantize(Decimal("0.01"))

    def get_price_for_user(self, user=None, pricing=None):
        """سعر البيع للمستخدم الحالي (تجزئة إذا كان زائراً أو بلا ملف عميل)"""
        tier = 'retail'
        if user is not None and getattr(user, 'is_authenticated', False):
            profile = getattr(user, 'customer_profile', None)
            if profile is not None:
                tier = profile.get_price_tier()
        return self.get_price(tier, pricing)

    @property
    def price(self):
        """سعر التجزئة - للتوافق مع الكود القديم الذي يستخدم product.price"""
        return self.get_price('retail')

    @property
    def wholesale_price(self):
        return self.get_price('wholesale')

    @property
    def super_wholesale_price(self):
        return self.get_price('super_wholesale')