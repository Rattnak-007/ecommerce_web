from rest_framework import viewsets
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Feature_Product, Category
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Customer, Category, Product, Order, Payment, Cart, CartItem, Feature_Product
from .serializers import (
    CustomerSerializer, CategorySerializer, ProductSerializer, OrderSerializer,
    PaymentSerializer, CartSerializer, FeatureProductSerializer
)
from django.views.generic import ListView, FormView, TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password
from .models import Customer
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from collections import defaultdict
from django.core.files.storage import default_storage

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

class FeatureProductViewSet(viewsets.ModelViewSet):
    queryset = Feature_Product.objects.all()
    serializer_class = FeatureProductSerializer

class ProductListView(ListView):
    model = Product
    template_name = 'ecommerce/products.html'
    context_object_name = 'products'

class RegisterPageView(TemplateView):
    template_name = 'ecommerce/register.html'

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        from .models import Customer
        if Customer.objects.filter(name=name).exists():
            return render(request, self.template_name, {'error': 'Username already exists'})
        customer = Customer.objects.create_user(
            name=name,
            email=email,
            password=password,
            phone=phone,
            address=address,
            is_staff=False
        )
        login(request, customer)
        return redirect('products')

class AboutPageView(TemplateView):
    template_name = 'ecommerce/about.html'

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        # Check if user already exists
        from .models import Customer
        if Customer.objects.filter(name=name).exists():
            return render(request, self.template_name, {'error': 'Username already exists'})
        # Always create non-staff user
        customer = Customer.objects.create_user(
            name=name,
            email=email,
            password=password,
            phone=phone,
            address=address,
            is_staff=False
        )
        login(request, customer)
        return redirect('products')  # Go to shopping/products page after register

class LoginPageView(TemplateView):
    template_name = 'ecommerce/login.html'

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, name=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')  # Admins go to admin dashboard
            else:
                return redirect('products')  # Users go to shopping/products page
        return render(request, self.template_name, {'error': 'Invalid credentials'})

class CartView(LoginRequiredMixin, TemplateView):
    template_name = 'ecommerce/cart.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            cart = Cart.objects.get(customer=self.request.user)
            cart_items = CartItem.objects.filter(cart=cart)
            cart_total = sum(item.product.price * item.quantity for item in cart_items)
        except Cart.DoesNotExist:
            cart_items = []
            cart_total = 0
        context['cart_items'] = cart_items
        context['cart_total'] = cart_total
        return context

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            token, _ = Token.objects.get_or_create(user=customer)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                customer = Customer.objects.get(name=serializer.validated_data['username'])
                if check_password(serializer.validated_data['password'], customer.password):
                    token, _ = Token.objects.get_or_create(user=customer)
                    return Response({'token': token.key}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
            except Customer.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HomeView(TemplateView):
    template_name = 'ecommerce/index.html'

    def dispatch(self, request, *args, **kwargs):
        # Redirect staff users to admin dashboard
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Product, Category
        featured_products = Feature_Product.objects.filter(is_available=True).order_by('-created_at')[:8]
        categories = Category.objects.filter(is_visible=True)
        context['featured_products'] = featured_products
        context['featured_categories'] = categories
        return context

class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ecommerce/admin-dashboard/dashboard.html'
    login_url = 'login'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from .models import Category, Product, Feature_Product
        # Add Category
        if 'add_category' in request.POST:
            name = request.POST.get('category_name')
            is_visible = request.POST.get('category_visible') == 'true'
            if name and not Category.objects.filter(name=name).exists():
                Category.objects.create(name=name, is_visible=is_visible)
                
        if 'add_product' in request.POST:
            name = request.POST.get('product_name')
            category_id = request.POST.get('product_category')
            price = request.POST.get('product_price')
            stock = request.POST.get('product_stock')
            description = request.POST.get('product_description')
            image = request.FILES.get('product_image')
            if name and category_id and price and stock:
                try:
                    category = Category.objects.get(pk=category_id)
                    product = Product(
                        name=name,
                        category=category,
                        price=price,
                        stock=stock,
                        description=description or "",
                        is_available=True,
                    )
                    if image:
                        product.image = image
                    product.save()
                except Category.DoesNotExist:
                    pass

        # Add Feature Product
        if 'add_feature_product' in request.POST:
            name = request.POST.get('feature_name')
            category_id = request.POST.get('feature_category')
            price = request.POST.get('feature_price')
            discount = request.POST.get('feature_discount') or 0
            stock = request.POST.get('feature_stock')
            description = request.POST.get('feature_description')
            image = request.FILES.get('feature_image')
            if name and category_id and price and stock:
                try:
                    category = Category.objects.get(pk=category_id)
                    feature_product = Feature_Product(
                        name=name,
                        category=category,
                        price=price,
                        discount=discount,
                        stock=stock,
                        description=description or "",
                        is_available=True,
                    )
                    if image:
                        feature_product.image = image
                    feature_product.save()
                except Category.DoesNotExist:
                    pass

        return redirect('admin_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Feature_Product
        customers = Customer.objects.all()
        products = Product.objects.all()
        feature_products = Feature_Product.objects.all()
        orders = Order.objects.all()
        payments = Payment.objects.all()
        categories = Category.objects.all()
        carts = Cart.objects.all()
        # Group orders by status
        order_status_counts = defaultdict(int)
        for o in orders:
            order_status_counts[o.status] += 1
        # Group payments by status
        payment_status_counts = defaultdict(int)
        for p in payments:
            payment_status_counts[p.status] += 1
        # Products per category (fix: use related_name 'products' instead of 'product_set')
        products_per_category = {cat.name: cat.products.count() for cat in categories}
        context.update({
            'customers': customers,
            'products': products,
            'feature_products': feature_products,
            'orders': orders,
            'payments': payments,
            'categories': categories,
            'carts': carts,
            'order_status_counts': dict(order_status_counts),
            'payment_status_counts': dict(payment_status_counts),
            'products_per_category': products_per_category,
        })
        return context

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'ecommerce/orders.html'
    context_object_name = 'orders'
    login_url = 'login'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(customer=user)

class CategoryListView(ListView):
    model = Category
    template_name = 'ecommerce/categories.html'
    context_object_name = 'categories'
    queryset = Category.objects.filter(is_visible=True)

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'ecommerce/category_detail.html'
    context_object_name = 'category'
    pk_url_kwarg = 'category_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        context['products'] = category.products.all()
        context['feature_products'] = category.feature_products.all()
        return context

class OrderDetailView(DetailView):
    model = Order
    template_name = 'ecommerce/order.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def add_to_cart(request, product_id):
    from .models import Product, Cart, CartItem
    product = get_object_or_404(Product, pk=product_id)
    cart, created = Cart.objects.get_or_create(customer=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"Added another {product.name} to your cart.")
    else:
        messages.success(request, f"Added {product.name} to your cart.")
    return redirect('cart')

class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'ecommerce/checkout.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart.objects.get(customer=self.request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_total = sum(item.product.price * item.quantity for item in cart_items)
        context['cart_items'] = cart_items
        context['cart_total'] = cart_total
        return context

@login_required
def update_cart(request):
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                item_id = key.split('_')[1]
                try:
                    item = CartItem.objects.get(cart_item_id=item_id, cart__customer=request.user)
                    quantity = int(value)
                    if quantity > 0:
                        item.quantity = quantity
                        item.save()
                except CartItem.DoesNotExist:
                    continue
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    CartItem.objects.filter(cart_item_id=item_id, cart__customer=request.user).delete()
    return redirect('cart')

@login_required
def book_cart(request):
    from .models import Cart, CartItem, Order
    cart = Cart.objects.get(customer=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    # Only allow booking if cart has items and user has not already booked/unpaid
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')
    # Prevent booking if there is an unpaid order for this user
    unpaid_order_exists = Order.objects.filter(customer=request.user, payment_status='unpaid').exists()
    if unpaid_order_exists:
        messages.error(request, "You have an unpaid order. Please complete payment before booking another cart.")
        return redirect('orders')
    order = Order.objects.create(
        customer=request.user,
        booking_reference=get_random_string(12),
        amount=sum(item.product.price * item.quantity for item in cart_items),
        status='pending',
        payment_status='unpaid',
        start_date=None,  # Set as needed
        end_date=None     # Set as needed
    )
    for item in cart_items:
        order.products.add(item.product)
    cart_items.delete()  # Clear cart after booking
    messages.success(request, "Booking successful! Your order has been placed.")
    return redirect('orders')

def generate_unique_booking_reference():
    from .models import Order
    while True:
        ref = get_random_string(12)
        if not Order.objects.filter(booking_reference=ref).exists():
            return ref

@login_required
def process_payment(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        cart = Cart.objects.get(customer=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect('checkout')
        # Create order with unique booking_reference
        order = Order.objects.create(
            customer=request.user,
            booking_reference=generate_unique_booking_reference(),
            amount=sum(item.product.price * item.quantity for item in cart_items),
            status='pending',
            payment_status='unpaid',
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timezone.timedelta(days=7)).date(),
        )
        for item in cart_items:
            order.products.add(item.product)
        # Create payment
        payment = Payment.objects.create(
            payment_reference=get_random_string(12),
            amount=order.amount,
            payment_method=payment_method,
            status='completed',
            customer=request.user,
            order=order
        )
        cart_items.delete()
        messages.success(request, "Payment successful! Thank you for your order.")
        return redirect('orders')
    return redirect('checkout')

def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url='login')(view_func)

@staff_required
def admin_edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    categories = Category.objects.all()
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.description = request.POST.get('description')
        category_id = request.POST.get('category')
        if category_id:
            product.category = get_object_or_404(Category, pk=category_id)
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.is_available = bool(request.POST.get('is_available'))
        product.save()
        messages.success(request, "Product updated successfully.")
        return redirect('admin_dashboard')
    return render(request, 'ecommerce/admin-dashboard/edit_product.html', {'product': product, 'categories': categories})

@staff_required
def admin_delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect('admin_dashboard')
    return redirect('admin_dashboard')

@staff_required
def admin_edit_feature_product(request, feature_product_id):
    feature_product = get_object_or_404(Feature_Product, pk=feature_product_id)
    categories = Category.objects.all()
    if request.method == 'POST':
        feature_product.name = request.POST.get('name')
        feature_product.price = request.POST.get('price')
        feature_product.discount = request.POST.get('discount')
        feature_product.stock = request.POST.get('stock')
        feature_product.description = request.POST.get('description')
        category_id = request.POST.get('category')
        if category_id:
            feature_product.category = get_object_or_404(Category, pk=category_id)
        if 'image' in request.FILES:
            feature_product.image = request.FILES['image']
        feature_product.is_available = bool(request.POST.get('is_available'))
        feature_product.save()
        messages.success(request, "Feature product updated successfully.")
        return redirect('admin_dashboard')
    return render(request, 'ecommerce/admin-dashboard/edit_feature_product.html', {'feature_product': feature_product, 'categories': categories})

@staff_required
def admin_delete_feature_product(request, feature_product_id):
    feature_product = get_object_or_404(Feature_Product, pk=feature_product_id)
    if request.method == 'POST':
        feature_product.delete()
        messages.success(request, "Feature product deleted successfully.")
        return redirect('admin_dashboard')
    return redirect('admin_dashboard')

about = AboutPageView.as_view()
