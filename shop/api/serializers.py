from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from shop.models import (
    Category, Coupon, Customer, Order, OrderItem, PaymentMethod,
    Product, ProductImage, ShippingMethod,
)

User = get_user_model()


# ---------- دوال مساعدة للكوبونات ----------

def get_valid_coupon(code):
    now = timezone.now()
    return Coupon.objects.filter(
        code__iexact=(code or '').strip(),
        active=True,
        valid_from__lte=now,
        valid_to__gte=now,
    ).first()


def apply_discount(coupon, subtotal):
    if coupon.discount_type == 'percentage':
        discount = subtotal * coupon.discount_value / Decimal('100')
    else:
        discount = coupon.discount_value
    discount = min(discount, subtotal)
    return (subtotal - discount).quantize(Decimal('0.01'))


# ---------- الأقسام والمنتجات ----------

class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'children']

    def get_children(self, obj):
        return CategoryMiniSerializer(obj.children.all(), many=True).data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductListSerializer(serializers.ModelSerializer):
    category = CategoryMiniSerializer(read_only=True)
    in_stock = serializers.BooleanField(source='is_available', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image', 'category',
                  'rating', 'reviews_count', 'in_stock']


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    colors_list = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            'model', 'description', 'specifications',
            'colors', 'colors_list', 'video', 'images',
        ]

    def get_colors_list(self, obj):
        if not obj.colors:
            return []
        text = obj.colors.replace('،', ',').replace('/', ',')
        return [c.strip() for c in text.split(',') if c.strip()]


# ---------- الحسابات ----------

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'city']

    def get_full_name(self, obj):
        return obj.first_name or obj.username

    def get_phone(self, obj):
        profile = getattr(obj, 'customer_profile', None)
        return profile.phone if profile else ''

    def get_city(self, obj):
        profile = getattr(obj, 'customer_profile', None)
        return profile.city if profile else ''


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('هذا البريد الإلكتروني مسجل مسبقاً')
        return value

    def validate_phone(self, value):
        value = value.strip()
        if Customer.objects.filter(phone=value).exists():
            raise serializers.ValidationError('رقم الهاتف مسجل مسبقاً')
        return value

    @transaction.atomic
    def create(self, data):
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password'],
            first_name=data['full_name'],
        )
        Customer.objects.create(
            user=user,
            phone=data['phone'],
            city=data.get('city') or 'عدن',
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


# ---------- الطلبات ----------

class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_available=True)
    )
    quantity = serializers.IntegerField(min_value=1, max_value=10000)


class OrderCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=50)
    address = serializers.CharField()
    phone = serializers.CharField(max_length=20)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    items = OrderItemInputSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        code = attrs.get('coupon_code')
        attrs['coupon'] = None
        if code:
            coupon = get_valid_coupon(code)
            if not coupon:
                raise serializers.ValidationError({'coupon_code': 'كود الخصم غير صالح أو منتهي'})
            attrs['coupon'] = coupon
        return attrs

    @transaction.atomic
    def create(self, data):
        user = self.context['request'].user
        items = data['items']
        subtotal = sum((i['product'].price * i['quantity'] for i in items), Decimal('0'))
        coupon = data['coupon']
        total = apply_discount(coupon, subtotal) if coupon else subtotal

        order = Order.objects.create(
            user=user,
            customer=getattr(user, 'customer_profile', None),
            full_name=data['full_name'],
            city=data['city'],
            address=data['address'],
            phone=data['phone'],
            total_price=total,
        )
        OrderItem.objects.bulk_create([
            OrderItem(order=order, product=i['product'],
                      price=i['product'].price, quantity=i['quantity'])
            for i in items
        ])
        return order


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['product_id', 'product_name', 'product_image',
                  'price', 'quantity', 'line_total']

    def get_product_image(self, obj):
        img = obj.product.image
        if not img:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(img.url) if request else img.url

    def get_line_total(self, obj):
        return str(obj.get_total_price())


class OrderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'full_name', 'city', 'address', 'phone',
                  'total_price', 'status', 'status_display', 'created_at', 'items']


# ---------- الشحن والدفع ----------

class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = ['id', 'name', 'company_name', 'cost',
                  'estimated_days', 'covered_cities']


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'payment_type', 'instructions']
