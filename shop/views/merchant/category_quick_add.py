from django.http import JsonResponse
from django.views.decorators.http import require_POST

from shop.models.category import Category
from shop.views.merchant.staff_required import staff_required


@staff_required
@require_POST
def category_quick_add(request):
    name = (request.POST.get('name') or '').strip()
    parent_id = request.POST.get('parent') or None
    if not name:
        return JsonResponse({'ok': False, 'error': 'اسم التصنيف مطلوب'}, status=400)

    parent = None
    if parent_id:
        parent = Category.objects.filter(pk=parent_id).first()
        if parent is None:
            return JsonResponse({'ok': False, 'error': 'التصنيف الأب غير موجود'}, status=400)

    if Category.objects.filter(name__iexact=name, parent=parent).exists():
        return JsonResponse({'ok': False, 'error': 'هذا التصنيف موجود مسبقاً في نفس المكان'}, status=400)

    cat = Category.objects.create(name=name, parent=parent)
    return JsonResponse({'ok': True, 'id': cat.pk, 'label': cat.full_path()})