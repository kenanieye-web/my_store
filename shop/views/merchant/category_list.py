from django.shortcuts import render, redirect
from shop.models import Category
from shop.views.merchant.staff_required import staff_required

@staff_required
def merchant_category_list(request):
    """إدارة وعرض تصنيفات المنتجات للتاجر"""
    categories = Category.objects.all().order_by('-id')
    main_categories = Category.objects.filter(parent__isnull=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        parent_id = request.POST.get('parent')
        
        if name:
            parent_category = None
            if parent_id:
                parent_category = Category.objects.get(id=parent_id)
                
            Category.objects.create(
                name=name,
                parent=parent_category
            )
            return redirect('merchant_category_list')
            
    context = {
        'categories': categories,
        'main_categories': main_categories,
    }
    return render(request, 'shop/merchant_category_list.html', context)