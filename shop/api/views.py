from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from rest_framework import generics, parsers, permissions
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.models import Category, Order, PaymentMethod, PricingSettings, Product, ShippingMethod
from shop.models.product_request import ProductRequestImage
from shop.utils.shipping import calculate_shipping_cost

from .serializers import (
    CategorySerializer, LoginSerializer, OrderCreateSerializer, OrderSerializer,
    PaymentMethodSerializer, ProductDetailSerializer, ProductListSerializer,
    ProductRequestSerializer, RegisterSerializer, ShippingMethodSerializer,
    ShippingQuoteSerializer, UserSerializer,
    apply_discount, get_valid_coupon,
)

User = get_user_model()


def get_user_tier(user):
    """مستوى السعر للمستخدم: retail / wholesale / super_wholesale"""
    if user is not None and user.is_authenticated:
        profile = getattr(user, 'customer_profile', None)
        if profile is not None:
            return profile.get_price_tier()
    return 'retail'


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 60


class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related('children')


class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination

    ORDERING = {
        # الترتيب بالتكلفة يعطي نفس ترتيب سعر البيع لأن النسبة ثابتة
        'price': 'cost_price',
        '-price': '-cost_price',
        'newest': '-created_at',
        'rating': '-rating',
    }

    def get_queryset(self):
        qs = Product.objects.select_related('category')
        p = self.request.query_params

        category = p.get('category')
        if category:
            # يقبل الرقم أو الـ slug، ويشمل الفئة وفروعها
            cond = Q(category__slug=category) | Q(category__parent__slug=category)
            if category.isdigit():
                cond |= Q(category_id=category) | Q(category__parent_id=category)
            qs = qs.filter(cond)

        q = p.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(model__icontains=q) | Q(description__icontains=q))

        # فلتر السعر: نحوّل سعر البيع المطلوب إلى تكلفة حسب نسبة مستوى العميل
        margin = PricingSettings.get_solo().get_margin(get_user_tier(self.request.user))
        factor = Decimal('1') + Decimal(margin) / Decimal('100')
        for param, lookup in (('min_price', 'cost_price__gte'), ('max_price', 'cost_price__lte')):
            value = p.get(param)
            if value:
                try:
                    qs = qs.filter(**{lookup: Decimal(value) / factor})
                except InvalidOperation:
                    pass

        return qs.order_by(self.ORDERING.get(p.get('ordering'), '-created_at'))


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.select_related('category').prefetch_related('images')


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data}, status=201)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip()
        found = User.objects.filter(email__iexact=email).first()
        user = None
        if found:
            user = authenticate(request, username=found.email,
                                password=serializer.validated_data['password'])
        if not user:
            return Response({'detail': 'البريد الإلكتروني أو كلمة المرور غير صحيحة'}, status=400)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data})


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return (Order.objects.filter(user=self.request.user)
                .select_related('shipping_method', 'payment_method')
                .prefetch_related('items__product'))

    def get_serializer_class(self):
        return OrderCreateSerializer if self.request.method == 'POST' else OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        data = OrderSerializer(order, context={'request': request}).data
        return Response(data, status=201)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (Order.objects.filter(user=self.request.user)
                .select_related('shipping_method', 'payment_method')
                .prefetch_related('items__product'))


class CouponValidateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get('code', '')
        try:
            subtotal = Decimal(str(request.data.get('subtotal', '0')))
        except InvalidOperation:
            subtotal = Decimal('0')
        coupon = get_valid_coupon(code) if code else None
        if not coupon:
            return Response({'valid': False, 'detail': 'كود الخصم غير صالح أو منتهي'}, status=400)
        total = apply_discount(coupon, subtotal)
        return Response({'valid': True, 'discount': str(subtotal - total), 'total': str(total)})


class ShippingMethodListView(generics.ListAPIView):
    serializer_class = ShippingMethodSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = ShippingMethod.objects.filter(is_active=True)


class ShippingQuoteView(APIView):
    """يحسب تكلفة كل طريقة شحن بالـ CBM لمحتويات السلة، للمدينة المحددة."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = ShippingQuoteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        city = s.validated_data.get('city', '')
        items = [(i['product'], i['quantity']) for i in s.validated_data['items']]
        quotes = []
        for m in ShippingMethod.objects.filter(is_active=True):
            if not m.covers_city(city):
                continue
            r = calculate_shipping_cost(items, m)
            quotes.append({
                'id': m.id,
                'name': m.name,
                'company_name': m.company_name,
                'cost': str(r['cost']),
                'delivery_days': r['delivery_days'],
                'total_cbm': str(r['total_cbm']),
            })
        quotes.sort(key=lambda q: Decimal(q['cost']))
        return Response(quotes)


class PaymentMethodListView(generics.ListAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = PaymentMethod.objects.filter(is_active=True)


class ProductRequestCreateView(generics.CreateAPIView):
    """طلب منتج غير متوفر (يقبل الزائر غير المسجل، وحتى 5 صور)."""
    serializer_class = ProductRequestSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    MAX_IMAGES = 5

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        files = request.FILES.getlist('images')
        if len(files) > self.MAX_IMAGES:
            return Response({'images': [f'الحد الأقصى {self.MAX_IMAGES} صور']}, status=400)

        customer = None
        if request.user.is_authenticated:
            customer = getattr(request.user, 'customer_profile', None)

        product_request = serializer.save(customer=customer)
        for f in files:
            ProductRequestImage.objects.create(request=product_request, image=f)
        return Response(self.get_serializer(product_request).data, status=201)