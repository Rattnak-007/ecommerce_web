from django.db import models


from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class CustomerManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Customer(AbstractBaseUser, PermissionsMixin):
    customer_id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=False, blank=True)
    name = models.CharField(max_length=100, unique=True)  # <-- Add unique=True here
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # important for admin login

    objects = CustomerManager()

    USERNAME_FIELD = 'name'  # use name for login
    REQUIRED_FIELDS = ['email']  # email is no longer required for superuser

    def __str__(self):
        return self.name




class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    stock = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    rating = models.FloatField(default=0)
    available_from = models.DateField(null=True, blank=True)
    available_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        Category,
        to_field='category_id',
        on_delete=models.CASCADE,
        db_column='category_id'
    )

    def __str__(self):
        return self.name


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    booking_reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed')
    ], default='pending')
    payment_status = models.CharField(max_length=50, choices=[
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded')
    ], default='unpaid')
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    customer = models.ForeignKey(
        Customer,
        to_field='customer_id',
        on_delete=models.CASCADE,
        db_column='customer_id'
    )
    products = models.ManyToManyField(Product, related_name='orders')

    @property
    def total(self):
        # If you have an OrderItem model (with quantity and price):
        if hasattr(self, 'items'):
            return sum(item.product.price * item.quantity for item in self.items.all())
        # Otherwise, fallback to amount field
        return self.amount

    def __str__(self):
        return f"Order #{self.order_id}"


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    payment_reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)  # e.g. Credit Card, Paypal
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ])

    customer = models.ForeignKey(
        Customer,
        to_field='customer_id',
        on_delete=models.CASCADE,
        db_column='customer_id'
    )
    order = models.OneToOneField(
        Order,
        to_field='order_id',
        on_delete=models.CASCADE,
        db_column='order_id'
    )

    def __str__(self):
        return f"Payment #{self.payment_id}"


class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    updated_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(
        Customer,
        to_field='customer_id',
        on_delete=models.CASCADE,
        db_column='customer_id'
    )

    def __str__(self):
        return f"Cart #{self.cart_id}"


class CartItem(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    quantity = models.PositiveIntegerField(default=1)

    cart = models.ForeignKey(
        Cart,
        to_field='cart_id',
        on_delete=models.CASCADE,
        db_column='cart_id'
    )
    product = models.ForeignKey(
        Product,
        to_field='product_id',
        on_delete=models.CASCADE,
        db_column='product_id'
    )

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Cart #{self.cart_id}"
