from django.contrib import admin
from .models import Customer, Category, Product, Order, Payment, Cart, CartItem

admin.site.register(Customer)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(Cart)
admin.site.register(CartItem)