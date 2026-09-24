import pandas as pd
from django.http import HttpResponse


def download_template(name):
    # إنشاء ملف إكسل فارغ بالأعمدة المطلوبة للمنتجات
    df = pd.DataFrame(columns=['name', 'price', 'category', 'is_available'])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment.filename=product_template.xlsx'
    df.to_excel(response, index=False)
    return response
