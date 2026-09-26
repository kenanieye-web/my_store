from django.shortcuts import render, redirect
from django.contrib import messages
from shop.models import Product
import pandas as pd


def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file)
            for _, row in df.iterrows():
                Product.objects.create(
                    name=row.get('name'),
                    price=row.get('price'),
                    is_available=row.get('is_available', True)
                )
            messages.success(request, "تم استيراد المنتجات بنجاح!")
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء الاستيراد: {e}")
        return redirect('merchant_product_list')
    
    return render(request, 'shop/import_excel.html')


# تعريف دالة مطابقة للرابط الذي يطلبه القالب لتجنب أي أخطاء
def import_product_from_url(request):
    return import_excel(request)