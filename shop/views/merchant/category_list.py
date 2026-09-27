from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from shop.models import Category
from shop.views.merchant.staff_required import staff_required


@staff_required
def merchant_category_list(request):
    """إدارة وعرض تصنيفات المنتجات للتاجر: إضافة، تعديل، حذف"""
    categories = Category.objects.all().order_by('-id')
    main_categories = Category.objects.filter(parent__isnull=True)

    if request.method == 'POST':
        action = request.POST.get('action', 'add')

        if action == 'add':
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
                messages.success(request, 'تمت إضافة التصنيف بنجاح')

        elif action == 'edit':
            category = get_object_or_404(Category, pk=request.POST.get('category_id'))
            name = request.POST.get('name')
            parent_id = request.POST.get('parent')

            if name:
                # منع اختيار التصنيف نفسه كتصنيف رئيسي له
                if parent_id and int(parent_id) == category.id:
                    messages.error(request, 'لا يمكن اختيار التصنيف نفسه كتصنيف رئيسي له')
                else:
                    category.name = name
                    category.parent = Category.objects.get(id=parent_id) if parent_id else None
                    category.save()
                    messages.success(request, 'تم تحديث التصنيف بنجاح')

        elif action == 'delete':
            category = get_object_or_404(Category, pk=request.POST.get('category_id'))
            category.delete()
            messages.success(request, 'تم حذف التصنيف')

        return redirect('merchant_category_list')

    context = {
        'categories': categories,
        'main_categories': main_categories,
    }
    return render(request, 'shop/merchant/merchant_category_list.html', context)