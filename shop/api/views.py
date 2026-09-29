from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.models import Category, Order, PaymentMethod, Product, ShippingMethod

from .serializers import (
    CategorySerializer, LoginSerializer, OrderCreateSerializer, OrderSerializer,
    PaymentMethodSerializer, ProductDetailSerializer, ProductListSerializer,
    RegisterSerializer, ShippingMethodSerializer, UserSerializer,
    apply_discount, get_valid_coupon,
)

User = get_user_model()


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
        'price': 'price',
        '-price': '-price',
        'newest': '-created_at',
        'rating': '-rating',
    }

    def get_queryset(self):
        qs = Product.objects.select_related('category')
        p = self.request.query_params

        category = p.get('category')
        if category:
            qs = qs.filter(Q(category__slug=category) | Q(category__parent__slug=category))

        q = p.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(model__icontains=q) | Q(description__icontains=q))

        for param, lookup in (('min_price', 'price__gte'), ('max_price', 'price__lte')):
            value = p.get(param)
            if value:
                try:
                    qs = qs.filter(**{lookup: Decimal(value)})
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


class PaymentMethodListView(generics.ListAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = PaymentMethod.objects.filter(is_active=True)
