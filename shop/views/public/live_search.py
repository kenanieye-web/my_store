from django.shortcuts import render
from shop.models import Product
from django.http import JsonResponse
def live_search(request):
    """إرجاع نتائج البحث الفوري بصيغة JSON للـ AJAX"""
    query = request.GET.get('q', '')
    products = []
    if query:
        product_objs = Product.objects.filter(name__icontains=query, is_available=True)[:5]
        for p in product_objs:
            products.append({
                'id': p.id,
                'name': p.name,
                'price': float(p.price),
                'image_url': p.image.url if p.image else '',
                'url': p.get_absolute_url() if hasattr(p, 'get_absolute_url') else f'/product/{p.id}/'
            })
    return JsonResponse({'products': products})


# --- إدارة سلة التسوق ---   
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'shop/product_detail.html', context)
