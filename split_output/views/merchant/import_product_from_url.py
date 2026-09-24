from django.shortcuts import redirect
from django.contrib import messages
from shop.models import Product, Category
import requests
from bs4 import BeautifulSoup
import re

from shop.views.merchant.staff_required import staff_required


@staff_required
def import_product_from_url(request):
    """استيراد وسحب بيانات المنتج تلقائياً عبر الرابط برمجياً دون تدخل يدوي"""
    if request.method == 'POST':
        url = request.POST.get('product_url', '').strip()
        if not url:
            messages.error(request, "يرجى إدخال رابط المنتج بشكل صحيح.")
            return redirect('merchant_product_list')

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        try:
            # جلب صفحة المنتج برمجياً
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                messages.error(request, "فشل الاتصال برابط المنتج، تأكد من صحة الرابط.")
                return redirect('merchant_product_list')
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. استخراج العنوان تلقائياً
            title_tag = soup.find('meta', property='og:title') or soup.find('h1')
            if title_tag:
                title = title_tag.get('content') if title_tag.name == 'meta' else title_tag.text
                title = title.strip()[:150]
            else:
                title = "منتج مستورد تلقائياً"
                
            # 2. استخراج السعر تلقائياً وتنظيفه من الرموز
            price = 0.00
            price_tag = soup.find('meta', property='product:price:amount') or soup.find('span', {'class': lambda x: x and 'price' in x.lower()})
            if price_tag:
                price_text = price_tag.get('content') if price_tag.name == 'meta' else price_tag.text
                numbers = re.findall(r'\d+\.\d+|\d+', price_text)
                if numbers:
                    price = float(numbers[0])
                    
            # 3. اختيار تصنيف افتراضي تلقائياً لتجنب أي أخطاء
            default_category = Category.objects.first()
            if not default_category:
                messages.error(request, "يجب أن تضيف تصنيفاً واحداً على الأقل في المتجر قبل الاستيراد.")
                return redirect('merchant_product_list')

            # 4. حفظ المنتج في قاعدة البيانات برمجياً وبشكل مفعل مباشرة
            product = Product.objects.create(
                name=title,
                price=price,
                category=default_category,
                is_available=True, # مفعل وجاهز للظهور في المتجر فوراً
            )
            
            messages.success(request, f"تم سحب وحفظ المنتج ({title}) بالسعر {price} بنجاح تلقائياً!")
            return redirect('merchant_product_list')

        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء السحب البرمجي: {str(e)}")
            return redirect('merchant_product_list')

    return redirect('merchant_product_list')
