from rest_framework import generics, permissions, parsers
from rest_framework.response import Response
from rest_framework import status
from shop.models.customer import Customer
from shop.models.product_request import ProductRequestImage
from .serializers import ProductRequestSerializer

MAX_IMAGES = 5


class ProductRequestCreateView(generics.CreateAPIView):
    serializer_class = ProductRequestSerializer
    permission_classes = [permissions.AllowAny]   # الزائر غير المسجل يستطيع الطلب
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        files = request.FILES.getlist('images')
        if len(files) > MAX_IMAGES:
            return Response({'images': [f'الحد الأقصى {MAX_IMAGES} صور']},
                            status=status.HTTP_400_BAD_REQUEST)

        customer = None
        if request.user.is_authenticated:
            customer = Customer.objects.filter(user=request.user).first()  # عدّل اسم الحقل إن اختلف

        product_request = serializer.save(customer=customer)
        for f in files:
            ProductRequestImage.objects.create(request=product_request, image=f)

        return Response(self.get_serializer(product_request).data,
                        status=status.HTTP_201_CREATED)