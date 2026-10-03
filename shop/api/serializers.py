from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from shop.models import (
    Category, Coupon, Customer, Order, OrderItem, PaymentMethod,
    PricingSettings, Product, ProductImage, ShippingMethod,
)
from shop.models.product_request import ProductRequest, ProductRequestImage
from shop.utils.shipping import calculate_shipping_cost

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


class CategoryChildSerializer(serializers.ModelSerializer):
    """فئة فرعية مع صورتها (تُستخدم داخل CategorySerializer فقط)"""

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image']


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'children']

    def get_children(self, obj):
        # تمرير context ليصل رابط الصورة كاملاً (https://...) لا نسبياً
        return CategoryChildSerializer(
            obj.children.all(), many=True, context=self.context
        ).data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductListSerializer(serializers.ModelSerializer):
    category = CategoryMiniSerializer(read_only=True)
    in_stock = serializers.BooleanField(source='is_available', read_only=True)
    # السعر = التكلفة + نسبة الربح حسب مستوى العميل (تجزئة للزائر)
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image', 'category',
                  'rating', 'reviews_count', 'in_stock',
                  'brand', 'created_at']

    def get_price(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        pricing = self.context.get('_pricing')
        if pricing is None:
            pricing = PricingSettings.get_solo()
            self.context['_pricing'] = pricing  # استعلام واحد لكل طلب
        return str(obj.get_price_for_user(user, pricing))


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    colors_list = serializers.SerializerMethodField()
    cbm = serializers.SerializerMethodField()
    carton_cbm = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            'model', 'description', 'specifications',
            'colors', 'colors_list', 'video', 'images',
            'length_cm', 'width_cm', 'height_cm', 'weight_kg',
            'units_per_carton', 'carton_length_cm', 'carton_width_cm',
            'carton_height_cm', 'carton_weight_kg', 'cbm', 'carton_cbm',
        ]

    def get_colors_list(self, obj):
        if not obj.colors:
            return []
        text = obj.colors.replace('،', ',').replace('/', ',')
        return [c.strip() for c in text.split(',') if c.strip()]

    def get_cbm(self, obj):
        return str(obj.get_cbm())

    def get_carton_cbm(self, obj):
        return str(obj.get_carton_cbm())


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


class ShippingQuoteSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True, allow_empty=False)
    city = serializers.CharField(required=False, allow_blank=True)


class OrderCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=50)
    address = serializers.CharField()
    phone = serializers.CharField(max_length=20)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    shipping_method = serializers.PrimaryKeyRelatedField(
        queryset=ShippingMethod.objects.filter(is_active=True)
    )
    payment_method = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.filter(is_active=True)
    )
    items = OrderItemInputSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        code = attrs.get('coupon_code')
        attrs['coupon'] = None
        if code:
            coupon = get_valid_coupon(code)
            if not coupon:
                raise serializers.ValidationError({'coupon_code': 'كود الخصم غير صالح أو منتهي'})
            attrs['coupon'] = coupon

        if not attrs['shipping_method'].covers_city(attrs['city']):
            raise serializers.ValidationError(
                {'shipping_method': 'طريقة الشحن هذه لا تغطي مدينتك'})
        return attrs

    @transaction.atomic
    def create(self, data):
        user = self.context['request'].user
        items = data['items']
        # سعر كل قطعة حسب مستوى العميل (تجزئة / جملة / جملة الجملة)
        pricing = PricingSettings.get_solo()
        unit_prices = [i['product'].get_price_for_user(user, pricing) for i in items]
        subtotal = sum(
            (p * i['quantity'] for p, i in zip(unit_prices, items)), Decimal('0')
        )
        coupon = data['coupon']
        goods_total = apply_discount(coupon, subtotal) if coupon else subtotal

        shipping = calculate_shipping_cost(
            [(i['product'], i['quantity']) for i in items],
            data['shipping_method'],
        )

        order = Order.objects.create(
            user=user,
            customer=getattr(user, 'customer_profile', None),
            full_name=data['full_name'],
            city=data['city'],
            address=data['address'],
            phone=data['phone'],
            shipping_method=data['shipping_method'],
            payment_method=data['payment_method'],
            shipping_cost=shipping['cost'],
            total_price=goods_total + shipping['cost'],
        )
        OrderItem.objects.bulk_create([
            OrderItem(order=order, product=i['product'],
                      price=p, quantity=i['quantity'],
                      supplier_store_number=i['product'].supplier_store_number)
            for p, i in zip(unit_prices, items)
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
    shipping_method_name = serializers.SerializerMethodField()
    payment_method_name = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'full_name', 'city', 'address', 'phone',
                  'total_price', 'shipping_cost', 'shipping_method_name',
                  'payment_method_name', 'status', 'status_display',
                  'created_at', 'items']

    def get_shipping_method_name(self, obj):
        return obj.shipping_method.name if obj.shipping_method else ''

    def get_payment_method_name(self, obj):
        return obj.payment_method.name if obj.payment_method else ''


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


# ---------- طلب منتج غير متوفر ----------

class ProductRequestImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRequestImage
        fields = ['id', 'image']


class ProductRequestSerializer(serializers.ModelSerializer):
    images = ProductRequestImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductRequest
        fields = [
            'id', 'full_name', 'phone', 'product_name', 'specifications',
            'quantity', 'approximate_price', 'video_url', 'notes',
            'status', 'created_at', 'images',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'images']
        # الاسم والهاتف يؤخذان من حساب العميل إن لم يرسلهما التطبيق
        extra_kwargs = {
            'full_name': {'required': False, 'allow_blank': True},
            'phone': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            if not validated_data.get('full_name'):
                validated_data['full_name'] = user.first_name or user.username
            if not validated_data.get('phone'):
                profile = getattr(user, 'customer_profile', None)
                validated_data['phone'] = profile.phone if profile else ''
        return super().create(validated_data)

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("الكمية يجب أن تكون 1 على الأقل")
        return value