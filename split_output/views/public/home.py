from django.shortcuts import render
from shop.models import Product, Category


def home(request):
    """الواجهة الرئيسية للمتجر"""
    categories = Category.objects.filter(parent=None)[:4]
    latest_products = Product.objects.filter(is_available=True).select_related('category').order_by('-id')[:6]
    
    context = {
        'categories': categories,
        'latest_products': latest_products,
    }
    return render(request, 'shop/home.html', context)
