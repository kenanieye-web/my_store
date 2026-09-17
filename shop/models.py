from django.db import models
from django.conf import settings
from django.utils.text import slugify


# 1. نموذج التصنيفات (مجموعات رئيسية وفرعية)
class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم التصنيف")
    slug = models.SlugField(unique=True, null=True, blank=True, verbose_name="الرابط (Slug)")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="التصنيف الرئيسي"
    )

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "التصنيفات"

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name

    def is_main_category(self):
        """التحقق مما إذا كان التصنيف رئيسياً"""
        return self.parent is None

    def save(self, *args, **kwargs):
        """توليد الـ Slug تلقائياً في حال عدم إدخاله"""
        if not self.slug and self.name:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


# 2. نموذج العملاء (لفصل العميل عن حسابات إدارة المتجر)
class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        verbose_name="حساب المستخدم"
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, null=True, verbose_name="العنوان")
    city = models.CharField(max_length=100, default='عدن', verbose_name="المدينة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الانضمام")

    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"

    def __str__(self):
        return f"عميل: {self.user.username}"


# 3. نموذج المنتجات
class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم المنتج")
    model = models.CharField(max_length=100, blank=True, null=True, verbose_name="الموديل")
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name="التصنيف"
    )
    description = models.TextField(blank=True, verbose_name="الوصف")
    specifications = models.TextField(blank=True, null=True, verbose_name="المواصفات الفنية")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="الصورة الرئيسية")
    video = models.FileField(upload_to='products/videos/', blank=True, null=True, verbose_name="فيديو المنتج", help_text="يمكنك رفع فيديو للمنتج (MP4)")
    is_available = models.BooleanField(default=True, verbose_name="متاح للبيع")
    stock = models.IntegerField(default=0, verbose_name="المخزون")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

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


# 3-أ. نموذج الصور الإضافية للمنتج (معرض الصور)
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, 
        related_name='images', 
        on_delete=models.CASCADE, 
        verbose_name="المنتج"
    )
    image = models.ImageField(upload_to='products/gallery/', verbose_name="الصورة الإضافية")

    class Meta:
        verbose_name = "صورة إضافية"
        verbose_name_plural = "معرض صور المنتجات"

    def __str__(self):
        return f"صورة إضافية لـ {self.product.name}"


# 4. نموذج السلة وعناصرها
class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "سلة تسوق"
        verbose_name_plural = "سلات التسوق"

    def __str__(self):
        return f"سلة #{self.id}"

    def get_total_price(self):
        """حساب إجمالي السعر لجميع العناصر داخل السلة"""
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        """حساب إجمالي عدد القطع في السلة"""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, 
        related_name='items', 
        on_delete=models.CASCADE, 
        verbose_name="السلة"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")

    class Meta:
        verbose_name = "عنصر السلة"
        verbose_name_plural = "عناصر السلة"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        """حساب السعر الإجمالي للعنصر بناءً على الكمية"""
        return self.product.price * self.quantity


# 5. نموذج الطلبات وعناصرها
class Order(models.Model):
    STATUS_CHOICES = (
        ('new', 'جديد'),
        ('shipping', 'جاري الشحن'),
        ('delivered', 'تم التوصيل'),
        ('canceled', 'ملغى'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="المستخدم"
    )
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="العميل"
    )
    full_name = models.CharField(max_length=100, verbose_name="اسم العميل")
    city = models.CharField(max_length=50, verbose_name="المدينة")
    address = models.TextField(verbose_name="العنوان")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر الكلي")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='new', 
        verbose_name="حالة الطلب"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت وتاريخ الطلب")

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب #{self.id} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        related_name='items', 
        on_delete=models.CASCADE, 
        verbose_name="الطلب"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")

    class Meta:
        verbose_name = "عنصر الطلب"
        verbose_name_plural = "عناصر الطلبات"

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (طلب #{self.order.id})"

    def get_total_price(self):
        """حساب الإجمالي للسطر الخاص بهذا المنتج في الطلب"""
        return self.price * self.quantity