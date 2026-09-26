"""
سكربت فحص شامل لكل المسارات (URLs) في مشروع Django.

طريقة الاستخدام:
1. انسخ هذا الملف إلى جذر المشروع (بجانب manage.py) في my_store.
2. شغّل الأمر التالي من نفس المجلد:

   python manage.py shell < check_all_urls.py

   أو (على PowerShell قد تحتاج هذه الصيغة بدلاً منها):

   Get-Content check_all_urls.py | python manage.py shell

ملاحظات مهمة قبل التشغيل:
- تأكد أن قاعدة البيانات تحتوي على بيانات كافية (منتج واحد على الأقل، تصنيف واحد،
  عميل واحد ... إلخ) حتى تعمل المسارات التي تحتوي على <int:pk> بدون خطأ "غير موجود".
- المسارات التي تحتاج تسجيل دخول (login required) ستُسجَّل كـ 302 (إعادة توجيه لصفحة
  تسجيل الدخول) وهذا أمر طبيعي، وليس خطأً.
- ركّز فقط على أي سطر يظهر فيه 500 أو ERROR — هذا هو الخطأ الحقيقي الذي يستحق الإصلاح.
"""

import django
from django.conf import settings
from django.urls import get_resolver
from django.test import Client
from django.urls.resolvers import URLPattern, URLResolver
import re

# السماح مؤقتاً بمضيف الاختبار الافتراضي لـ Django Test Client أثناء هذا الفحص فقط.
# هذا لا يعدّل settings.py على القرص، فقط يعدّل القيمة في الذاكرة لمدة هذا التشغيل.
if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]


def collect_urls(resolver=None, prefix=""):
    """يجمع كل المسارات القابلة للاختبار (بدون باراميترات ديناميكية غير محلولة)."""
    if resolver is None:
        resolver = get_resolver()

    results = []
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            new_prefix = prefix + str(pattern.pattern)
            results.extend(collect_urls(pattern, new_prefix))
        elif isinstance(pattern, URLPattern):
            full_pattern = prefix + str(pattern.pattern)
            results.append((full_pattern, pattern.name))
    return results


def fill_placeholders(url_pattern):
    """
    يستبدل الباراميترات الديناميكية في المسار بقيم افتراضية (1) لتجربة الرابط.
    مثال: /product/<int:pk>/  →  /product/1/
    """
    url = url_pattern

    # إزالة أنماط regex الخاصة بالبداية/النهاية إن وجدت
    url = url.replace("^", "").replace("$", "")

    # استبدال أنواع الباراميترات الشائعة بقيمة افتراضية
    url = re.sub(r"<int:\w+>", "1", url)
    url = re.sub(r"<str:\w+>", "test", url)
    url = re.sub(r"<slug:\w+>", "test-slug", url)
    url = re.sub(r"<uuid:\w+>", "00000000-0000-0000-0000-000000000000", url)
    url = re.sub(r"<path:\w+>", "1", url)
    url = re.sub(r"<uidb64>", "MQ", url)
    url = re.sub(r"<token>", "test-token", url)

    if not url.startswith("/"):
        url = "/" + url

    return url


def main():
    client = Client()
    urls = collect_urls()

    print("=" * 90)
    print(f"عدد المسارات المكتشفة: {len(urls)}")
    print("=" * 90)

    results_500 = []
    results_404 = []
    results_other_error = []
    results_ok = []

    seen = set()

    for pattern, name in urls:
        # تجاهل مسارات admin الداخلية الخاصة بـ django نفسها لتوفير الوقت (اختياري)
        # علّق السطرين التاليين إذا أردت فحص admin أيضاً
        if pattern.startswith("admin/") and "shop" not in pattern:
            continue

        url = fill_placeholders(pattern)

        # تفادي تكرار فحص نفس الرابط مرتين
        if url in seen:
            continue
        seen.add(url)

        try:
            response = client.get(url, follow=False)
            status = response.status_code
        except Exception as e:
            results_other_error.append((url, name, f"EXCEPTION: {e}"))
            print(f"[EXCEPTION] {url:<50} name={name}  ->  {e}")
            continue

        if status == 500:
            results_500.append((url, name))
            print(f"[500 ERROR] {url:<50} name={name}")
        elif status == 404:
            results_404.append((url, name))
            print(f"[404]       {url:<50} name={name}")
        elif status in (200, 301, 302):
            results_ok.append((url, name, status))
            print(f"[{status}]       {url:<50} name={name}")
        else:
            results_other_error.append((url, name, status))
            print(f"[{status}]       {url:<50} name={name}")

    print("\n" + "=" * 90)
    print("ملخص النتائج")
    print("=" * 90)
    print(f"✅ يعمل بشكل طبيعي (200/301/302): {len(results_ok)}")
    print(f"⚠️  غير موجود (404): {len(results_404)}")
    print(f"❌ خطأ سيرفر (500): {len(results_500)}")
    print(f"❓ حالات أخرى/استثناءات: {len(results_other_error)}")

    if results_500:
        print("\n--- المسارات التي بها خطأ 500 (تحتاج إصلاح فوري) ---")
        for url, name in results_500:
            print(f"  - {url}   (name={name})")

    if results_404:
        print("\n--- المسارات التي أعطت 404 (تحقق إذا كانت تحتاج بيانات في قاعدة البيانات) ---")
        for url, name in results_404:
            print(f"  - {url}   (name={name})")


main()