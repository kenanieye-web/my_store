import django.db.models.signals


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
