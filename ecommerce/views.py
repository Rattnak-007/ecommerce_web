from rest_framework import viewsets
from .models import Customer, Category, Product, Order, Payment, Cart, CartItem
from .serializers import CustomerSerializer, CategorySerializer, ProductSerializer, OrderSerializer, PaymentSerializer, CartSerializer
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
        # Check if user already exists
        from .models import Customer
        if Customer.objects.filter(name=name).exists():
            return render(request, self.template_name, {'error': 'Username already exists'})
        customer = Customer.objects.create_user(
            name=name,
            email=email,
            password=password,
            phone=phone,
            address=address
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
        # Remove redirect to 'admin_dashboard'
        return super().dispatch(request, *args, **kwargs)

class AdminDashboardView(TemplateView):
    template_name = 'ecommerce/admin.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers_count'] = Customer.objects.count()
        context['products_count'] = Product.objects.count()
        context['orders_count'] = Order.objects.count()
        context['payments_count'] = Payment.objects.count()
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
    if cart_items:
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
    messages.error(request, "Your cart is empty.")
    return redirect('cart')

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
    return redirect('checkout')
