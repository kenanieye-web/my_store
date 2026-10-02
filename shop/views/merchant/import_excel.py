import io
import os
import posixpath
import re
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.text import slugify
from PIL import Image
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import column_index_from_string, coordinate_from_string
from openpyxl.worksheet.datavalidation import DataValidation

from shop.models import Category, Product, ProductImage


# ======================================================================
# قائمة الأعمدة الوحيدة: يستخدمها تحميل القالب والاستيراد معاً
# (المفتاح، عنوان العمود، عرض العمود)
# الأعمدة الاثنا عشر الأولى هي نفس ترتيب ملفك القديم، والجديدة بعدها
# ======================================================================
COLUMNS = [
    ("id", "ID (منتج جديد)", 14),
    ("name", "اسم المنتج", 28),
    ("model", "الموديل", 16),
    ("category", "التصنيف", 20),
    ("description", "الوصف", 40),
    ("specifications", "المواصفات الفنية", 40),
    ("cost_price", "سعر التكلفة", 12),
    ("is_available", "متاح للبيع (نعم/لا)", 16),
    ("stock", "المخزون", 10),
    ("image_url", "رابط الصورة", 24),
    ("image", "صورة المنتج", 18),
    ("box_image", "صورة العلبة", 18),
    # ----- أعمدة جديدة -----
    ("brand", "الماركة", 16),
    ("subcategory", "المجموعة الفرعية", 20),
    ("length_cm", "الطول (سم)", 12),
    ("width_cm", "العرض (سم)", 12),
    ("height_cm", "الارتفاع (سم)", 12),
    ("weight_kg", "الوزن (كغم)", 12),
    ("units_per_carton", "عدد القطع في الكرتون", 14),
    ("carton_length_cm", "طول الكرتون (سم)", 14),
    ("carton_width_cm", "عرض الكرتون (سم)", 14),
    ("carton_height_cm", "ارتفاع الكرتون (سم)", 14),
    ("carton_weight_kg", "وزن الكرتون (كغم)", 14),
]

LABELS = {key: label for key, label, _ in COLUMNS}

DECIMAL_FIELDS = (
    "length_cm", "width_cm", "height_cm", "weight_kg",
    "carton_length_cm", "carton_width_cm", "carton_height_cm", "carton_weight_kg",
)
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024


def _staff_only(user):
    return user.is_authenticated and user.is_active and user.is_staff


# ---------------------------------------------------------------- الأعمدة
def _norm(text):
    """تطبيع عنوان العمود: حذف ما بين الأقواس والمسافات الزائدة."""
    text = re.sub(r"\(.*?\)", "", str(text))
    return " ".join(text.split()).lower()


KEY_BY_HEADER = {_norm(label): key for key, label, _ in COLUMNS}


def _header_key(header):
    h = _norm(header)
    if h.startswith("id"):          # يقبل: ID / ID منتج جديد / ID (منتج جديد)
        return "id"
    if h in ("السعر", "price"):     # توافق مع ملفات Excel القديمة
        return "cost_price"
    return KEY_BY_HEADER.get(h)


# ---------------------------------------------------------------- قراءة القيم
def _s(row, key):
    v = row.get(key, "")
    s = "" if v is None else str(v).strip()
    # خلايا الأخطاء أو الصور المدمجة تصل كـ nan أو #VALUE! فتُعامل كخلية فارغة
    return "" if s.lower() in ("nan", "#value!") else s


def _dec(row, key):
    s = _s(row, key).replace(",", "")
    if not s:
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError(f"قيمة غير صحيحة في عمود «{LABELS[key]}»: {s}")


def _int(row, key):
    d = _dec(row, key)
    return None if d is None else int(d)


def _bool(row, key):
    s = _s(row, key).lower()
    if not s:
        return None
    if s in ("نعم", "yes", "y", "true", "1"):
        return True
    if s in ("لا", "no", "n", "false", "0"):
        return False
    raise ValueError(f"قيمة غير صحيحة في عمود «{LABELS[key]}» (المسموح: نعم/لا): {s}")


# ---------------------------------------------------------------- الصور
def _read_zip(zip_file):
    """اسم الملف (بأحرف صغيرة) -> (الاسم الأصلي، البيانات)."""
    files = {}
    if not zip_file:
        return files
    with zipfile.ZipFile(zip_file) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            base = os.path.basename(info.filename)
            if not base or base.startswith("."):      # يتجاوز ملفات __MACOSX
                continue
            files[base.lower()] = (base, z.read(info))
    return files


def _find_image(files, ref):
    """يقبل اسم الصورة بامتداد أو بدون امتداد (S-137 أو S-137.jpg)."""
    ref = os.path.basename(ref.strip()).lower()
    if not ref:
        return None
    if ref in files:
        return files[ref]
    for ext in IMAGE_EXTENSIONS:
        if ref + ext in files:
            return files[ref + ext]
    return None


def _download(url):
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("الرابط يجب أن يبدأ بـ http أو https")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": url})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = r.read(MAX_DOWNLOAD_BYTES + 1)
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise ValueError("حجم الصورة أكبر من 5MB")
    # التأكد أن الرابط لصورة فعلية وليس لصفحة ويب
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        fmt = (img.format or "").lower()
    except Exception:
        raise ValueError("الرابط ليس رابط صورة مباشراً (افتح الصورة نفسها وانسخ رابطها)")
    ext = ".jpg" if fmt in ("jpeg", "") else f".{fmt}"
    return f"image{ext}", data


# ---------------------------------------------------------------- الصور المدمجة داخل الإكسل
_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def _zip_target(base_dir, target):
    if target.startswith("/"):
        return target[1:]
    return posixpath.normpath(posixpath.join(base_dir, target))


def _first_sheet_path(z):
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rid = wb.find("{*}sheets/{*}sheet").get(_REL_NS)
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    for rel in rels:
        if rel.get("Id") == rid:
            return _zip_target("xl", rel.get("Target"))
    return "xl/worksheets/sheet1.xml"


def _in_cell_pictures(z, result):
    """صور «وضع الصورة داخل الخلية» (Place in Cell) في إكسل 365."""
    needed = ("xl/metadata.xml", "xl/richData/rdrichvalue.xml",
              "xl/richData/rdrichvaluestructure.xml", "xl/richData/richValueRel.xml")
    names = set(z.namelist())
    if not all(n in names for n in needed):
        return

    # cell vm -> valueMetadata -> futureMetadata(rvb) -> rich value -> rel -> media
    meta = ET.fromstring(z.read("xl/metadata.xml"))
    rvb_of_bk = []
    for fm in meta.findall("{*}futureMetadata"):
        if fm.get("name") == "XLRICHVALUE":
            for bk in fm.findall("{*}bk"):
                rvb = next((e for e in bk.iter() if e.tag.endswith("}rvb")), None)
                rvb_of_bk.append(int(rvb.get("i")) if rvb is not None else None)
    value_meta = meta.find("{*}valueMetadata")
    v_of_vm = [int(bk.find("{*}rc").get("v")) for bk in value_meta.findall("{*}bk")]

    structs = [
        [k.get("n") for k in s.findall("{*}k")]
        for s in ET.fromstring(z.read("xl/richData/rdrichvaluestructure.xml")).findall("{*}s")
    ]
    rich_values = ET.fromstring(z.read("xl/richData/rdrichvalue.xml")).findall("{*}rv")

    rel_ids = [r.get(_REL_NS) for r in
               ET.fromstring(z.read("xl/richData/richValueRel.xml")).findall("{*}rel")]
    rel_target = {
        r.get("Id"): _zip_target("xl/richData", r.get("Target"))
        for r in ET.fromstring(z.read("xl/richData/_rels/richValueRel.xml.rels"))
    }

    sheet = ET.fromstring(z.read(_first_sheet_path(z)))
    for c in sheet.iterfind(".//{*}c"):
        vm = c.get("vm")
        if not vm:
            continue
        try:
            rvb_index = rvb_of_bk[v_of_vm[int(vm) - 1]]
            rv = rich_values[rvb_index]
            vals = rv.findall("{*}v")
            local_id = int(vals[structs[int(rv.get("s"))].index("_rvRel:LocalImageIdentifier")].text)
            media = rel_target[rel_ids[local_id]]
            col_letter, row_num = coordinate_from_string(c.get("r"))
            result[(row_num, column_index_from_string(col_letter))] = (
                posixpath.basename(media), z.read(media)
            )
        except Exception:
            continue


def _floating_pictures(raw, result):
    """الصور العائمة (Insert > Picture) المثبتة فوق خلية."""
    ws = load_workbook(io.BytesIO(raw)).worksheets[0]
    for img in getattr(ws, "_images", []):
        marker = getattr(img.anchor, "_from", None)
        if marker is None:
            continue
        ext = "jpg" if (img.format or "png").lower() == "jpeg" else (img.format or "png").lower()
        result.setdefault((marker.row + 1, marker.col + 1), (f"image.{ext}", img._data()))


def _embedded_images(raw):
    """{(رقم الصف، رقم العمود): (اسم الملف، البيانات)} — الترقيم يبدأ من 1."""
    result = {}
    try:
        _in_cell_pictures(zipfile.ZipFile(io.BytesIO(raw)), result)
    except Exception:
        pass
    try:
        _floating_pictures(raw, result)
    except Exception:
        pass
    return result


def _named(pic, prefix):
    """يعطي الصورة المدمجة اسماً مفهوماً بدل image1.png."""
    ext = os.path.splitext(pic[0])[1] or ".png"
    return (f"{prefix}{ext}", pic[1])


# ---------------------------------------------------------------- التصنيفات
def _resolve_category(main_name, sub_name):
    main = (
        Category.objects.filter(name=main_name, parent__isnull=True).first()
        or Category.objects.filter(name=main_name).first()
    )
    if not main:
        raise ValueError(f"التصنيف غير موجود: {main_name}")
    if sub_name:
        sub = Category.objects.filter(name=sub_name, parent=main).first()
        if not sub:
            raise ValueError(f"المجموعة الفرعية «{sub_name}» غير موجودة تحت «{main_name}»")
        return sub
    return main


# ---------------------------------------------------------------- استيراد صف
def _import_row(row, files, pics):
    """يعيد (الحالة، قائمة التنبيهات). الحالة: created / updated / None (صف فارغ)."""
    name = _s(row, "name")
    raw_id = _s(row, "id")
    if not name and not raw_id:
        return None, []

    # ID رقمي = تحديث منتج موجود، وفارغ (أو نص مثل "جديد") = منتج جديد
    product = None
    if raw_id:
        try:
            pk = int(float(raw_id))
        except ValueError:
            pk = None
        if pk is not None:
            product = Product.objects.filter(pk=pk).first()
            if not product:
                raise ValueError(f"لا يوجد منتج بالرقم {pk}")

    is_new = product is None
    if is_new:
        if not name:
            raise ValueError("اسم المنتج مطلوب")
        product = Product()

    # الحقول النصية (في التحديث لا تُمسح القيمة القديمة إذا كانت الخلية فارغة)
    if name:
        product.name = name
    for key in ("model", "brand", "description", "specifications"):
        v = _s(row, key)
        if v:
            setattr(product, key, v)

    cost_price = _dec(row, "cost_price")
    if cost_price is not None:
        product.cost_price = cost_price
    elif is_new:
        raise ValueError("سعر التكلفة مطلوب")

    main_name, sub_name = _s(row, "category"), _s(row, "subcategory")
    if main_name or sub_name:
        if not main_name:
            raise ValueError("اكتب التصنيف الرئيسي مع المجموعة الفرعية")
        product.category = _resolve_category(main_name, sub_name)
    elif is_new:
        raise ValueError("التصنيف مطلوب")

    available = _bool(row, "is_available")
    if available is not None:
        product.is_available = available
    for key in DECIMAL_FIELDS:
        d = _dec(row, key)
        if d is not None:
            setattr(product, key, d)
    stock = _int(row, "stock")
    if stock is not None:
        product.stock = stock
    units = _int(row, "units_per_carton")
    if units is not None:
        product.units_per_carton = max(units, 1)

    # صورة المنتج: مدمجة في الخلية أولاً، ثم اسم ملف في zip، ثم الرابط
    warnings = []
    prefix = slugify(_s(row, "model") or _s(row, "name"), allow_unicode=True) or "product"
    image = _named(pics["image"], prefix) if pics.get("image") else None
    image_ref = _s(row, "image")
    if not image and image_ref:
        image = _find_image(files, image_ref)
        if not image:
            warnings.append(f"صورة المنتج «{image_ref}» غير موجودة في ملف zip")
    if not image:
        url = _s(row, "image_url")
        if url:
            try:
                image = _named(_download(url), prefix)
            except Exception as e:
                warnings.append(f"تعذّر تحميل الصورة من الرابط: {e}")

    product.save()
    if image:
        product.image.save(image[0], ContentFile(image[1]), save=True)

    # صورة العلبة تُحفظ في معرض صور المنتج (مدمجة في الخلية أو اسم ملف في zip)
    box_ref = _s(row, "box_image")
    box = _named(pics["box_image"], prefix + "-box") if pics.get("box_image") else None
    if not box and box_ref:
        box = _find_image(files, box_ref)
        if not box:
            warnings.append(f"صورة العلبة «{box_ref}» غير موجودة في ملف zip")
    if box:
        gallery = ProductImage(product=product)
        gallery.image.save(box[0], ContentFile(box[1]), save=True)

    return ("created" if is_new else "updated"), warnings


# ---------------------------------------------------------------- الاستيراد
@user_passes_test(_staff_only)
def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            raw = request.FILES['excel_file'].read()
            df = pd.read_excel(io.BytesIO(raw), dtype=str, keep_default_na=False)
            files = _read_zip(request.FILES.get('images_zip'))
            embedded = _embedded_images(raw)
        except Exception as e:
            messages.error(request, f"تعذّرت قراءة الملفات: {e}")
            return redirect('merchant_product_list')

        df.columns = [_header_key(c) for c in df.columns]
        if "name" not in df.columns:
            messages.error(
                request,
                "لم أجد عمود «اسم المنتج» في الملف. حمّل القالب الجديد من الصفحة واستخدم عناوينه."
            )
            return redirect('merchant_product_list')

        col_of = {key: i + 1 for i, key in enumerate(df.columns) if key}
        created = updated = 0
        errors, warnings = [], []
        for idx, row in df.iterrows():
            line = idx + 2      # الصف الأول عناوين
            pics = {
                key: embedded.get((line, col_of[key]))
                for key in ("image", "box_image") if key in col_of
            }
            try:
                with transaction.atomic():         # كل صف مستقل: خطأ صف لا يلغي الباقي
                    status, row_warnings = _import_row(row, files, pics)
            except Exception as e:
                errors.append(f"سطر {line}: {e}")
                continue
            if status == "created":
                created += 1
            elif status == "updated":
                updated += 1
            warnings += [f"سطر {line}: {w}" for w in row_warnings]

        if created or updated:
            messages.success(request, f"تمت إضافة {created} منتج وتحديث {updated} منتج.")
        if warnings:
            messages.warning(request, "تنبيهات الصور: " + " | ".join(warnings[:10]))
        if errors:
            messages.error(
                request,
                f"تعذّر استيراد {len(errors)} صف: " + " | ".join(errors[:10])
            )
        if not (created or updated or errors):
            messages.info(request, "لم أجد أي صفوف لاستيرادها في الملف.")
        return redirect('merchant_product_list')

    return render(request, 'shop/merchant/import_excel.html')


# ---------------------------------------------------------------- تحميل القالب الفارغ
@user_passes_test(_staff_only)
def download_excel_template(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "المنتجات"
    ws.sheet_view.rightToLeft = True

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1B5299")
    for col, (_, label, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col, value=label)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "A2"

    # قائمة اختيار نعم/لا لعمود «متاح للبيع»
    avail_col = get_column_letter([k for k, _, _ in COLUMNS].index("is_available") + 1)
    dv = DataValidation(type="list", formula1='"نعم,لا"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{avail_col}2:{avail_col}2000")

    help_ws = wb.create_sheet("تعليمات")
    help_ws.sheet_view.rightToLeft = True
    help_ws.column_dimensions["A"].width = 110
    for i, line in enumerate([
        "تعليمات تعبئة الملف",
        "• الأعمدة المطلوبة للمنتج الجديد: اسم المنتج، التصنيف، سعر التكلفة. والباقي اختياري. أسعار البيع (تجزئة/جملة/جملة الجملة) تُحسب تلقائياً من نسب التسعير.",
        "• عمود ID: اتركه فارغاً لمنتج جديد، أو اكتب رقم منتج موجود لتحديثه (الخلايا الفارغة لا تمسح القيم القديمة).",
        "• التصنيف والمجموعة الفرعية: اكتب الاسم مطابقاً تماماً لما في المتجر. المجموعة الفرعية اختيارية.",
        "• متاح للبيع: نعم أو لا (الافتراضي نعم).",
        "• صورة المنتج وصورة العلبة: اكتب اسم ملف الصورة داخل ملف zip، بامتداد أو بدون (S-137 أو S-137.jpg).",
        "• رابط الصورة: يُستخدم فقط إذا لم توجد صورة المنتج في ملف zip.",
        "• الأبعاد بالسنتيمتر، والوزن بالكيلوغرام (مثال: 0.050 = 50 غرام). الفارغ يعني 0.",
        "• عدد القطع في الكرتون: الافتراضي 1.",
        "• الماركة: اختيارية، اكتبها كما تريدها أن تظهر في فلتر التطبيق (مثال: Dinks).",
        "• لا تغيّر عناوين الأعمدة، ويمكن تغيير ترتيبها.",
        "• أي صف فيه خطأ يُتجاوز مع رسالة توضح رقم السطر، ويُستورد باقي الصفوف.",
    ], start=1):
        c = help_ws.cell(row=i, column=1, value=line)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if i == 1:
            c.font = Font(bold=True, size=13)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="products_template.xlsx"'
    wb.save(response)
    return response


# تعريف دالة مطابقة للرابط الذي يطلبه القالب لتجنب أي أخطاء
def import_product_from_url(request):
    return import_excel(request)