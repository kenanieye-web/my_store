from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
import pandas as pd

from shop.models import Product
from shop.views.merchant.staff_required import staff_required


@staff_required
def bulk_product_actions(request):
    """تنفيذ إجراء جماعي (حذف أو تصدير Excel) على المنتجات المحددة من قائمة إدارة المنتجات"""
    if request.method != 'POST':
        return redirect('merchant_product_list')

    selected_ids = request.POST.getlist('selected_products')
    action = request.POST.get('action')

    if not selected_ids:
        messages.warning(request, "لم يتم تحديد أي منتج لتنفيذ الإجراء عليه.")
        return redirect('merchant_product_list')

    products = Product.objects.filter(id__in=selected_ids)

    if action == 'delete':
        count = products.count()
        products.delete()
        messages.success(request, f"تم حذف {count} منتج بنجاح.")
        return redirect('merchant_product_list')

    elif action == 'export':
        data = list(products.values(
            'id', 'name', 'model', 'category__name', 'price', 'stock',
            'is_available', 'description',
        ))
        df = pd.DataFrame(data)
        df.rename(columns={
            'id': 'المعرف',
            'name': 'اسم المنتج',
            'model': 'الموديل',
            'category__name': 'التصنيف',
            'price': 'السعر',
            'stock': 'المخزون',
            'is_available': 'متاح للبيع',
            'description': 'الوصف',
        }, inplace=True)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="selected_products.xlsx"'
        df.to_excel(response, index=False)
        return response

    messages.warning(request, "إجراء غير معروف.")
    return redirect('merchant_product_list')