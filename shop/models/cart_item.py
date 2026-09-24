import django.db.models.signals

from shop.models.cart import Cart
from shop.models.product import Product


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
