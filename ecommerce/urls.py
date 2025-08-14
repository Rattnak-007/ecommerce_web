from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet, CategoryViewSet, ProductViewSet, OrderViewSet, PaymentViewSet, CartViewSet,
    RegisterView, LoginView, ProductListView, CartView, HomeView,
    LoginPageView, RegisterPageView, AdminDashboardView, logout_view, CategoryListView, CategoryDetailView,
    add_to_cart, OrderDetailView, CheckoutView, update_cart, remove_from_cart, book_cart, process_payment,
    OrderListView, FeatureProductViewSet, about,
    admin_edit_product, admin_delete_product,
    admin_edit_feature_product, admin_delete_feature_product,
)
from . import views

router = DefaultRouter()
router.register('customers', CustomerViewSet)
router.register('categories', CategoryViewSet)
router.register('products', ProductViewSet)
router.register('orders', OrderViewSet)
router.register('payments', PaymentViewSet)
router.register('carts', CartViewSet)
router.register('feature-products', FeatureProductViewSet)

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),  # Index page at /
    path('api/', include(router.urls)),
    path('api/register/', RegisterView.as_view(), name='api_register'),  # API endpoint
    path('api/login/', LoginView.as_view(), name='api_login'),           # API endpoint

    path('login/', LoginPageView.as_view(), name='login'),           # HTML form
    path('register/', RegisterPageView.as_view(), name='register'),  # HTML form


    path('products/', ProductListView.as_view(), name='products'),
    path('cart/', CartView.as_view(), name='cart'),

    path('logout/', logout_view, name='logout'),  # <-- added logout path

    path('categories/', CategoryListView.as_view(), name='categories'),
    path('categories/<int:category_id>/', CategoryDetailView.as_view(), name='categories_detail'),

    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),

    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order_detail'),

    path('checkout/', CheckoutView.as_view(), name='checkout'),

    path('cart/update/', update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),

    path('cart/book/', book_cart, name='book_cart'),

    path('checkout/process/', process_payment, name='process_payment'),

    path('orders/', OrderListView.as_view(), name='orders'),
    path('about/', about, name='about'),

    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),

    path('admin-dashboard/product/edit/<int:product_id>/', admin_edit_product, name='admin_edit_product'),
    path('admin-dashboard/product/delete/<int:product_id>/', admin_delete_product, name='admin_delete_product'),
    path('admin-dashboard/feature-product/edit/<int:feature_product_id>/', admin_edit_feature_product, name='admin_edit_feature_product'),
    path('admin-dashboard/feature-product/delete/<int:feature_product_id>/', admin_delete_feature_product, name='admin_delete_feature_product'),
    path('admin-dashboard/order/edit/<int:order_id>/', views.admin_edit_order, name='admin_edit_order'),
    path('admin-dashboard/order/delete/<int:order_id>/', views.admin_delete_order, name='admin_delete_order'),
    path('admin-dashboard/payment/edit/<int:payment_id>/', views.admin_edit_payment, name='admin_edit_payment'),
    path('admin-dashboard/payment/delete/<int:payment_id>/', views.admin_delete_payment, name='admin_delete_payment'),
    path('admin-dashboard/category/edit/<int:category_id>/', views.admin_edit_category, name='admin_edit_category'),
    path('admin-dashboard/category/delete/<int:category_id>/', views.admin_delete_category, name='admin_delete_category'),
]


