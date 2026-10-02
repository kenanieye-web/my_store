from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from shop.models import Category
from shop.views.merchant.staff_required import staff_required


def _get_parent(parent_id):
    """يرجع (تصنيف الأب أو None، هل المعرّف صحيح)"""
    if not parent_id:
        return None, True
    parent = Category.objects.filter(pk=parent_id).first()
    return parent, parent is not None


@staff_required
def merchant_category_list(request):
    """إدارة تصنيفات المنتجات للتاجر: إضافة، تعديل، حذف (بعدد مستويات غير محدود)"""

    if request.method == 'POST':
        action = request.POST.get('action', 'add')

        if action == 'add':
            name = (request.POST.get('name') or '').strip()
            parent, ok = _get_parent(request.POST.get('parent'))
            if not name:
                messages.error(request, 'اسم التصنيف مطلوب')
            elif not ok:
                messages.error(request, 'التصنيف الرئيسي المختار غير موجود')
            elif Category.objects.filter(name__iexact=name, parent=parent).exists():
                messages.error(request, 'هذا التصنيف موجود مسبقاً في نفس المكان')
            else:
                Category.objects.create(name=name, parent=parent)
                messages.success(request, 'تمت إضافة التصنيف بنجاح')

        elif action == 'edit':
            category = get_object_or_404(Category, pk=request.POST.get('category_id'))
            name = (request.POST.get('name') or '').strip()
            parent, ok = _get_parent(request.POST.get('parent'))
            if not name:
                messages.error(request, 'اسم التصنيف مطلوب')
            elif not ok:
                messages.error(request, 'التصنيف الرئيسي المختار غير موجود')
            elif parent and parent.pk in category.self_and_descendant_ids():
                messages.error(request, 'لا يمكن جعل التصنيف تابعاً لنفسه أو لأحد فروعه')
            elif Category.objects.filter(name__iexact=name, parent=parent).exclude(pk=category.pk).exists():
                messages.error(request, 'يوجد تصنيف بنفس الاسم في هذا المكان')
            else:
                category.name = name
                category.parent = parent
                category.save()
                messages.success(request, 'تم تحديث التصنيف بنجاح')

        elif action == 'delete':
            category = get_object_or_404(Category, pk=request.POST.get('category_id'))
            if category.children.exists():
                messages.error(request, 'لا يمكن حذف تصنيف يحتوي تصنيفات فرعية، احذف الفروع أو انقلها أولاً')
            elif category.products.exists():
                messages.error(request, 'لا يمكن حذف تصنيف يحتوي منتجات، انقل المنتجات إلى تصنيف آخر أولاً')
            else:
                category.delete()
                messages.success(request, 'تم حذف التصنيف')

        return redirect('merchant_category_list')

    context = {
        # قائمة شجرية بكل التصنيفات: [(التصنيف, المستوى, المسار الكامل), ...]
        'category_tree': Category.tree(),
        'categories': Category.objects.select_related('parent').order_by('-id'),
        # للتوافق مع القالب الحالي إلى أن يُعدَّل
        'main_categories': Category.objects.all().order_by('name'),
    }
    return render(request, 'shop/merchant/merchant_category_list.html', context)