import django.db.models.signals
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
import django.db

# 0.نموذج المستخدم المخصص
class CustomUser(AbstractUser):
    email =django.db.models.EmailField(unique=True,verbose_name="البريد الالكتروني")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    class Meta:
        verbose_name="مستخدم"
        verbose_name_plural="المستخدمون"

    def __str__(self):
             return self.username
# 1. نموذج التصنيفات (مجموعات رئيسية وفرعية)
class Category(django.db.models.Model):
    name = django.db.models.CharField(max_length=200, verbose_name="اسم التصنيف")
    slug = django.db.models.SlugField(unique=True, null=True, blank=True, verbose_name="الرابط (Slug)")
    parent = django.db.models.ForeignKey(
        'self',
        on_delete=django.db.models.CASCADE,
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
            self.slug = slugify(self.name, allow_unicode=True) # type: ignore
        super().save(*args, **kwargs)


# 2. نموذج العملاء (لفصل العميل عن حسابات إدارة المتجر)
class Customer(django.db.models.Model):
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
    created_at = django.db.models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الانضمام")
    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"

    def __str__(self):
        return f"عميل: {self.user.username}"


@receiver(django.db.models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_profile(sender, instance, created, **kwargs) -> None:
    if created and not instance.is_staff and not instance.is_superuser:
        Customer.objects.create(user=instance)


# 3. نموذج المنتجات
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


# 3-أ. نموذج الصور الإضافية للمنتج (معرض الصور)
class ProductImage(django.db.models.Model):
    product = django.db.models.ForeignKey(
        Product, 
        related_name='images', 
        on_delete=django.db.models.CASCADE, 
        verbose_name="المنتج"
    )
    image = django.db.models.ImageField(upload_to='products/gallery/', verbose_name="الصورة الإضافية")

    class Meta:
        verbose_name = "صورة إضافية"
        verbose_name_plural = "معرض صور المنتجات"

    def __str__(self):
        return f"صورة إضافية لـ {self.product.name}"


# 4. نموذج السلة وعناصرها
class Cart(django.db.models.Model):
    created_at = django.db.models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

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


class CartItem(django.db.models.Model):
    cart = django.db.models.ForeignKey(
        Cart, 
        related_name='items', 
        on_delete=django.db.models.CASCADE, 
        verbose_name="السلة"
    )
    product = django.db.models.ForeignKey(Product, on_delete=django.db.models.CASCADE, verbose_name="المنتج")
    quantity = django.db.models.PositiveIntegerField(default=1, verbose_name="الكمية")

    class Meta:
        verbose_name = "عنصر السلة"
        verbose_name_plural = "عناصر السلة"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        """حساب السعر الإجمالي للعنصر بناءً على الكمية"""
        return self.product.price * self.quantity


# 5. نموذج الطلبات وعناصرها
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


class OrderItem(django.db.models.Model):
    order = django.db.models.ForeignKey(
        Order, 
        related_name='items', 
        on_delete=django.db.models.CASCADE, 
        verbose_name="الطلب"
    )
    product = django.db.models.ForeignKey(Product, on_delete=django.db.models.CASCADE, verbose_name="المنتج")
    price = django.db.models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    quantity = django.db.models.PositiveIntegerField(default=1, verbose_name="الكمية")

    class Meta:
        verbose_name = "عنصر الطلب"
        verbose_name_plural = "عناصر الطلبات"

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (طلب #{self.order.id})"

    def get_total_price(self):
        """حساب الإجمالي للسطر الخاص بهذا المنتج في الطلب"""
        return self.price * self.quantity