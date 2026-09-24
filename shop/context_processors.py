from shop.models import Category
from shop.models.cart import Cart  # تأكد من استيراد نموذج السلة حسب مساره لديك، أو من shop.models

def nav_categories(request):
    """الفئات الرئيسية مع فروعها لقائمة الهيدر في كل الصفحات."""
    return {'nav_categories': Category.objects.filter(parent=None).prefetch_related('children')}

def cart_summary(request):
    """عدد القطع في سلة الزائر (السلة محفوظة في session باسم cart_id)."""
    cart_id = request.session.get('cart_id')
    cart = Cart.objects.filter(id=cart_id).first() if cart_id else None
    return {'cart_count': cart.get_total_items() if cart else 0}