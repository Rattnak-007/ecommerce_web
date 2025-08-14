from django.contrib import admin
from .models import Customer, Category, Product, Order, Payment, Cart, CartItem, Feature_Product, SlideShow

admin.site.register(Customer)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Feature_Product)
admin.site.register(SlideShow)