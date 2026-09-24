from django.shortcuts import get_object_or_404
from shop.models import Product


def product_detail(request, pk):
    """عرض تفاصيل منتج محدد"""
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk, is_available=True)
    # جلب المنتجات المشابهة (نفس التصنيف، باستبعاد المنتج الحالي، وبحد أقصى 4 منتجات)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
