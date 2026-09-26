import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from shop.models import Order
from django.shortcuts import get_object_or_404

def export_orders_excel(request):
    # إنشاء ملف إكسل جديد للطلبات ككل
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "الطلبات"
    
    # رأس الأعمدة
    ws.append(["رقم الطلب", "المجموع", "الحالة", "تاريخ الإنشاء"])
    
    # جلب الطلبات وإضافتها
    orders = Order.objects.all()
    for order in orders:
        ws.append([order.id, getattr(order, 'total_price', 0), order.status, str(order.created_at)])
        
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=orders.xlsx'
    wb.save(response)
    return response

def export_orders_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=orders.pdf'
    
    p = canvas.Canvas(response, pagesize=letter)
    p.drawString(100, 750, "تقرير الطلبات - متجر كنان")
    
    orders = Order.objects.all()
    y = 700
    for order in orders:
        p.drawString(100, y, f"Order #{order.id} - Status: {order.status}")
        y -= 25
        if y < 50:
            p.showPage()
            y = 750
            
    p.save()
    return response

# ==========================================
# الدوال الجديدة الخاصة بتصدير طلب واحد محدد
# ==========================================

def export_single_order_excel(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Order_{order.id}"
    
    ws.append(["رقم الطلب", order.id])
    ws.append(["الحالة", order.status])
    ws.append(["تاريخ الإنشاء", str(order.created_at)])
    ws.append([])
    ws.append(["المنتج", "الكمية", "السعر"])
    
    # افتراض أن علاقة منتجات الطلب تدعم items (أو قم بتعديلها حسب هيكل نموذج الطلب لديك)
    for item in order.items.all():
        ws.append([item.product.name, item.quantity, item.price])
        
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=order_{order.id}.xlsx'
    wb.save(response)
    return response

def export_single_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=order_{order.id}.pdf'
    
    p = canvas.Canvas(response, pagesize=letter)
    p.drawString(100, 750, f"فاتورة الطلب رقم #{order.id}")
    p.drawString(100, 720, f"حالة الطلب: {order.status}")
    p.drawString(100, 690, f"التاريخ: {order.created_at}")
    
    y = 640
    p.drawString(100, y, "المنتجات:")
    y -= 25
    for item in order.items.all():
        p.drawString(120, y, f"- {item.product.name} (الكمية: {item.quantity})")
        y -= 20
        
    p.save()
    return response