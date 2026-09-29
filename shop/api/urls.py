from django.urls import path

from . import views

urlpatterns = [
    path('categories/', views.CategoryListView.as_view()),
    path('products/', views.ProductListView.as_view()),
    path('products/<int:pk>/', views.ProductDetailView.as_view()),
    path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('me/', views.MeView.as_view()),
    path('orders/', views.OrderListCreateView.as_view()),
    path('orders/<int:pk>/', views.OrderDetailView.as_view()),
    path('coupons/validate/', views.CouponValidateView.as_view()),
    path('shipping-methods/', views.ShippingMethodListView.as_view()),
    path('payment-methods/', views.PaymentMethodListView.as_view()),
]
