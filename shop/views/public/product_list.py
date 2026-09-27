from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from shop.models import Product, Category
from django.db.models import Q


def product_list(request, category_slug=None):
    """عرض المنتجات مع دعم البحث والتصفية حسب القسم"""
    products = Product.objects.filter(is_available=True).select_related('category')
    categories = Category.objects.filter(parent=None)
    current_category = None

    # الفلترة عبر رابط التصنيف المباشر (category/<slug>/)
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(Q(category=current_category) | Q(category__parent=current_category))

    # البحث باسم المنتج أو الوصف
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
        
    category_param = request.GET.get('category')
    if category_param:
        current_category = get_object_or_404(Category, slug=category_param)
        products = products.filter(Q(category=current_category) | Q(category__parent=current_category))
        
# الـ context و return يجب أن يكونا هنا (في مستوى بداية الدالة وليس داخل الـ if)
    # الترقيم الصفحي (Pagination): 12 منتج في كل صفحة
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': categories,
        'current_category': current_category,
        'selected_category': category_param,
        'search_query': search_query,
    }
    return render(request, 'shop/products/product_list.html', context)