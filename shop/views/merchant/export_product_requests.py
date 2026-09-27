import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from shop.models import ProductRequest


def export_product_request_excel(request, pk):
    """تصدير طلب منتج واحد إلى ملف Excel"""
    req = get_object_or_404(ProductRequest, pk=pk)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Request_{req.id}"

    ws.append(["رقم الطلب", req.id])
    ws.append(["مقدم الطلب", req.full_name])
    ws.append(["رقم الهاتف", req.phone])
    ws.append(["المنتج المطلوب", req.product_name])
    ws.append(["المواصفات", req.specifications or "—"])
    ws.append(["الكمية المطلوبة", req.quantity])
    ws.append(["السعر التقريبي", str(req.approximate_price) if req.approximate_price else "—"])
    ws.append(["رابط الفيديو", req.video_url or "—"])
    ws.append(["ملاحظات إضافية", req.notes or "—"])
    ws.append(["الحالة", req.get_status_display()])
    ws.append(["تاريخ الطلب", str(req.created_at)])
    ws.append([])
    ws.append(["عدد الصور المرفقة", req.images.count()])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=product_request_{req.id}.xlsx'
    wb.save(response)
    return response


def export_product_request_pdf(request, pk):
    """تصدير طلب منتج واحد إلى ملف PDF"""
    req = get_object_or_404(ProductRequest, pk=pk)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=product_request_{req.id}.pdf'

    p = canvas.Canvas(response, pagesize=letter)
    p.drawString(100, 750, f"طلب منتج غير متوفر رقم #{req.id}")
    p.drawString(100, 720, f"مقدم الطلب: {req.full_name}")
    p.drawString(100, 700, f"الهاتف: {req.phone}")
    p.drawString(100, 680, f"المنتج المطلوب: {req.product_name}")
    p.drawString(100, 660, f"الكمية المطلوبة: {req.quantity}")

    y = 640
    if req.approximate_price:
        p.drawString(100, y, f"السعر التقريبي: {req.approximate_price}")
        y -= 20
    if req.specifications:
        p.drawString(100, y, f"المواصفات: {req.specifications}")
        y -= 20
    if req.video_url:
        p.drawString(100, y, f"رابط الفيديو: {req.video_url}")
        y -= 20
    if req.notes:
        p.drawString(100, y, f"ملاحظات: {req.notes}")
        y -= 20

    p.drawString(100, y, f"الحالة: {req.get_status_display()}")
    y -= 20
    p.drawString(100, y, f"التاريخ: {req.created_at}")

    p.save()
    return response