import django.db.models.signals

from shop.models.order import Order
from shop.models.product import Product


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
