from django.shortcuts import render, get_object_or_404
from shop.models import Product, ShippingMethod
from shop.utils.shipping import calculate_shipping_cost


def product_detail(request, pk):
    """عرض تفاصيل منتج محدد"""
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk, is_available=True)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    # تحويل نص المواصفات الفنية إلى جدول (خاصية / قيمة) بدل أسطر متتالية
    specs_table = []
    if product.specifications:
        for line in product.specifications.splitlines():
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                specs_table.append((key.strip(), value.strip()))
            else:
                specs_table.append((None, line))

    # حساب أرخص تقدير شحن لهذا المنتج (كمية 1) لعرضه بجانب السعر
    shipping_estimate = None
    active_methods = ShippingMethod.objects.filter(is_active=True)
    if active_methods.exists():
        results = []
        for method in active_methods:
            result = calculate_shipping_cost([(product, 1)], method)
            results.append({
                'method_name': method.name,
                'cost': result['cost'],
                'delivery_days': result['delivery_days'],
            })
        shipping_estimate = min(results, key=lambda r: r['cost'])

    context = {
        'product': product,
        'related_products': related_products,
        'specs_table': specs_table,
        'shipping_estimate': shipping_estimate,
    }
    return render(request, 'shop/products/product_detail.html', context)