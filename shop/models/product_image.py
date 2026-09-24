import django.db.models.signals

from shop.models.product import Product


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
