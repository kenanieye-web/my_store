import openpyxl
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from shop.models import Order

from shop.admin.order_item_inline import OrderItemInline


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'full_name',
        'city',
        'phone',
        'total_price',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    inlines = [OrderItemInline]
    actions = ['export_orders_excel']
    change_form_template = (
        'admin/shop/order/change_form.html'  # قالب مخصص لإضافة زر الفاتورة
    )

    # 1. Action لتصدير الطلبات المحددة إلى Excel
    def export_orders_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Orders'

        # عناوين الأعمدة
        headers = [
            'رقم الطلب',
            'الاسم الكامل',
            'المدينة',
            'الهاتف',
            'المبلغ الإجمالي',
            'الحالة',
            'تاريخ الطلب',
        ]
        ws.append(headers)

        # إضافة بيانات الطلبات المحددة
        for order in queryset:
            ws.append([
                order.id,
                order.full_name,
                order.city,
                order.phone,
                str(order.total_price),
                order.status,
                (
                    order.created_at.strftime('%Y-%m-%d %H:%M')
                    if order.created_at
                    else ''
                ),
            ])

        response = HttpResponse(
            content_type=(
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        )
        response['Content-Disposition'] = (
            'attachment; filename=selected_orders.xlsx'
        )
        wb.save(response)
        return response

    export_orders_excel.short_description = (
        'تصدير الطلبات المحددة إلى ملف Excel'
    )

    # 2. إضافة مسار خاص لتوليد فاتورة PDF داخل لوحة التحكم
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/invoice-pdf/',
                self.admin_site.admin_view(self.generate_invoice_pdf),
                name='order-invoice-pdf',
            ),
        ]
        return custom_urls + urls

    # 3. دالة توليد ملف الـ PDF للطلب
    def generate_invoice_pdf(self, request, object_id):
        order = get_object_or_404(Order, pk=object_id)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename=invoice_order_{order.id}.pdf'
        )

        p = canvas.Canvas(response, pagesize=letter)
        p.setFont('Helvetica-Bold', 16)
        p.drawString(100, 750, f'Store Invoice - Order #{order.id}')

        p.setFont('Helvetica', 12)
        p.drawString(100, 710, f'Customer Name: {order.full_name}')
        p.drawString(100, 685, f'City: {order.city}')
        p.drawString(100, 660, f'Phone: {order.phone}')
        p.drawString(100, 635, f'Total Price: {order.total_price} $')
        p.drawString(
            100,
            610,
            f'Status: {order.status}',
        )

        p.showPage()
        p.save()
        return response

    # تمرير رابط الفاتورة للقالب الخاص بصفحة تفاصيل الطلب
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['has_pdf_invoice'] = True
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )