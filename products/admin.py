from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop', 'created_at']
    list_filter = ['shop', 'created_at']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'sale_price', 'stock', 'is_low_stock', 'shop']
    list_filter = ['category', 'shop', 'is_active', 'created_at']
    search_fields = ['name', 'barcode']
    readonly_fields = ['barcode', 'created_at', 'updated_at']
