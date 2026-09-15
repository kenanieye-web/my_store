from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.utils import timezone

from .models import Product, Category, Cart, CartItem, Order, OrderItem, Customer
from .forms import ProductForm

# --- الديكورات المخصصة والتحقق من الصلاحيات ---

def staff_required(view_func):
    """ديكور مخصص للتحقق من أن المستخدم من طاقم الإدارة (التاجر)"""
    def check_user(user):
        return user.is_authenticated and user.is_staff
    
    decorated_view = user_passes_test(
        check_user,
        login_url='login',
        redirect_field_name=None
    )(view_func)
    return decorated_view


# --- واجهات المتجر العامة (العملاء) ---

def home(request):
    """الواجهة الرئيسية للمتجر"""
    categories = Category.objects.filter(parent=None)[:4]
    latest_products = Product.objects.filter(is_available=True).select_related('category').order_by('-id')[:6]
    
    context = {
        'categories': categories,
        'latest_products': latest_products,
    }
    return render(request, 'shop/home.html', context)

def product_list(request):
    """عرض المنتجات مع دعم البحث والتصفية حسب القسم"""
    products = Product.objects.filter(is_available=True).select_related('category')
    categories = Category.objects.filter(parent=None)
    
    # البحث باسم المنتج أو الوصف
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
        
    # الفلترة حسب التصنيف (تشمل التصنيف الرئيسي والأقسام الفرعية التابعة له)
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(Q(category_id=category_id) | Q(category__parent_id=category_id))
        
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
    }
    return render(request, 'shop/product_list.html', context)

def product_detail(request, pk):
    """عرض تفاصيل منتج محدد"""
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk, is_available=True)
    return render(request, 'shop/product_detail.html', {'product': product})


# --- إدارة سلة التسوق ---

@transaction.atomic
def add_to_cart(request, product_id):
    """إضافة منتج إلى سلة التسوق أو تحديث الكمية"""
    if request.method != 'POST':
        return redirect('product_list')

    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart_id = request.session.get('cart_id')
    
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()
        if not cart:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    messages.success(request, f"تمت إضافة '{product.name}' إلى سلة التسوق بنجاح.")
    return redirect('cart_detail')

def cart_detail(request):
    """عرض محتويات سلة التسوق"""
    cart_id = request.session.get('cart_id')
    cart = None
    if cart_id:
        cart = Cart.objects.filter(id=cart_id).prefetch_related('items__product').first()
    return render(request, 'shop/cart_detail.html', {'cart': cart})

def remove_from_cart(request, item_id):
    """حذف عنصر محدد من السلة"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.info(request, f"تم حذف '{product_name}' من سلة التسوق.")
    return redirect('cart_detail')

def update_cart_quantity(request, item_id):
    """زيادة أو إنقاص كمية عنصر داخل السلة"""
    if request.method != 'POST':
        return redirect('cart_detail')

    cart_item = get_object_or_404(CartItem, id=item_id)
    action = request.POST.get('action')
    
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"تم تحديث كمية '{cart_item.product.name}'.")
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, f"تم تحديث كمية '{cart_item.product.name}'.")
        else:
            product_name = cart_item.product.name
            cart_item.delete()
            messages.info(request, f"تم حذف '{product_name}' من سلة التسوق.")
            
    return redirect('cart_detail')


# --- إتمام الشراء والطلبات ---

@transaction.atomic
def checkout(request):
    """صفحة إتمام الطلب الشراء"""
    cart_id = request.session.get('cart_id')
    cart = Cart.objects.filter(id=cart_id).prefetch_related('items__product').first() if cart_id else None

    if not cart or not cart.items.exists():
        messages.warning(request, "سلة التسوق فارغة!")
        return redirect('product_list')

    total_price = sum((item.get_total_price() for item in cart.items.all()), 0)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        city = request.POST.get('city', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not all([full_name, city, address, phone]):
            messages.error(request, "يرجى ملء جميع حقول الشحن المطلوبة.")
            return render(request, 'shop/checkout.html', {'cart': cart, 'total_price': total_price})

        customer_profile = getattr(request.user, 'customer_profile', None) if request.user.is_authenticated else None

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer=customer_profile,
            full_name=full_name,
            city=city,
            address=address,
            phone=phone,
            total_price=total_price
        )

        order_items = [
            OrderItem(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
            for item in cart.items.all()
        ]
        OrderItem.objects.bulk_create(order_items)

        cart.delete()
        if 'cart_id' in request.session:
            del request.session['cart_id']

        messages.success(request, f"تم إتمام طلبك بنجاح! رقم الطلب #{order.id}")
        return render(request, 'shop/order_success.html', {'order': order})

    return render(request, 'shop/checkout.html', {'cart': cart, 'total_price': total_price})


# --- نظام الحسابات والمستخدمين ---

def register_user(request):
    """تسجيل العميل وإنشاء حساب وحساب عميل متطابق"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        phone = request.POST.get('phone', '').strip()
        city = request.POST.get('city', 'عدن').strip()

        if not email or not password or not full_name:
            messages.error(request, "يرجى ملء جميع الحقول المطلوبة.")
        elif User.objects.filter(username=email).exists():
            messages.error(request, "هذا البريد الإلكتروني مسجل مسبقاً.")
        else:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=full_name,
                    is_staff=False,
                    is_superuser=False
                )
                
                Customer.objects.create(
                    user=user,
                    phone=phone,
                    city=city
                )

            login(request, user)
            messages.success(request, f"أهلاً بك يا {full_name}! تم إنشاء حسابك بنجاح.")
            return redirect('home')

    return render(request, 'shop/register.html')

def login_user(request):
    """تسجيل الدخول بالبريد الإلكتروني وكلمة المرور"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "مرحباً بك مجدداً!")
            return redirect('home')
        else:
            messages.error(request, "البريد الإلكتروني أو كلمة المرور غير صحيحة.")

    return render(request, 'shop/login.html')

def logout_user(request):
    """تسجيل الخروج"""
    logout(request)
    messages.info(request, "تم تسجيل الخروج بنجاح.")
    return redirect('home')

@login_required(login_url='login')
def customer_profile(request):
    """عرض سجل الطلبات الخاصة بالمستخدم المسجل"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/customer_profile.html', {'orders': orders})


# --- لوحة تحكم التاجر وإدارة المتجر (مخصصة للطاقم الإداري فقط) ---

@staff_required
def merchant_dashboard(request):
    """لوحة التحكم العامة للتاجر والإحصائيات السريعة"""
    products_count = Product.objects.count()
    customers_count = Customer.objects.count()
    total_orders_count = Order.objects.count()

    new_orders_count = Order.objects.filter(Q(status='new') | Q(status='جديد')).count()
    shipping_orders_count = Order.objects.filter(Q(status__in=['shipping', 'قيد الشحن', 'جاري الشحن', 'التوصيل'])).count()
    delivered_orders_count = Order.objects.filter(Q(status='delivered') | Q(status='تم التوصيل')).count()
    canceled_orders_count = Order.objects.filter(Q(status='canceled') | Q(status='ملغي') | Q(status='الملغية')).count()

    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    context = {
        'products_count': products_count,
        'customers_count': customers_count,
        'total_orders_count': total_orders_count,
        'new_orders_count': new_orders_count,
        'shipping_orders_count': shipping_orders_count,
        'delivered_orders_count': delivered_orders_count,
        'canceled_orders_count': canceled_orders_count,
        'recent_orders': recent_orders,
    }
    return render(request, 'shop/dashboard.html', context)

@staff_required
def sales_report(request):
    """تقارير المبيعات وتحليل الإيرادات"""
    completed_orders = Order.objects.filter(
        Q(status='delivered') | Q(status='تم التوصيل')
    ).order_by('-created_at')

    period = request.GET.get('period', 'all')
    now = timezone.now()

    if period == 'today':
        completed_orders = completed_orders.filter(created_at__date=now.date())
    elif period == 'week':
        start_of_week = now - timedelta(days=now.weekday())
        completed_orders = completed_orders.filter(created_at__gte=start_of_week)
    elif period == 'month':
        completed_orders = completed_orders.filter(
            created_at__year=now.year, 
            created_at__month=now.month
        )

    all_orders = Order.objects.all()
    total_sales = completed_orders.aggregate(total=Sum('total_price'))['total'] or 0
    
    top_selling_items = OrderItem.objects.filter(
        order__in=completed_orders
    ).values(
        'product__name', 'price'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    context = {
        'completed_orders': completed_orders,
        'total_sales': total_sales,
        'completed_count': completed_orders.count(),
        'total_orders_count': all_orders.count(),
        'top_selling_items': top_selling_items,
        'selected_period': period,
    }
    return render(request, 'shop/sales_report.html', context)

@staff_required
def customer_list(request):
    """عرض قائمة العملاء والبيانات المرتبطة بهم"""
    customers = Customer.objects.select_related('user').all().order_by('-id')
    return render(request, 'shop/customer_list.html', {'customers': customers})

@staff_required
def staff_user_list(request):
    """عرض طاقم الإدارة"""
    staff_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('-date_joined')
    return render(request, 'shop/staff_user_list.html', {'staff_users': staff_users})

@staff_required
def order_list(request):
    """قائمة جميع الطلبات للتاجر"""
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'shop/order_list.html', {'orders': orders})

@staff_required
def order_detail(request, pk):
    """تفاصيل الطلب وتحديث حالته"""
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
            messages.success(request, f"تم تحديث حالة الطلب #{order.id} بنجاح.")
            return redirect('order_detail', pk=order.id)

    return render(request, 'shop/order_detail.html', {'order': order})

@staff_required
def merchant_product_list(request):
    """إدارة المنتجات للتاجر"""
    products = Product.objects.select_related('category').all().order_by('-id')
    return render(request, 'shop/merchant_product_list.html', {'products': products})

@staff_required
def add_product(request):
    """إضافة منتج جديد"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "تم إضافة المنتج بنجاح!")
            return redirect('merchant_product_list')
    else:
        form = ProductForm()
    
    return render(request, 'shop/add_product.html', {'form': form})

@staff_required
def edit_product(request, pk):
    """تعديل بيانات منتج قائمة"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"تم تحديث المنتج '{product.name}' بنجاح!")
            return redirect('merchant_product_list')
    else:
        form = ProductForm(instance=product)
        
    return render(request, 'shop/edit_product.html', {'form': form, 'product': product})

@staff_required
def delete_product(request, pk):
    """حذف منتج"""
    product = get_object_or_404(Product, pk=pk)
    product_name = product.name
    product.delete()
    messages.success(request, f"تم حذف المنتج '{product_name}' بنجاح.")
    return redirect('merchant_product_list')