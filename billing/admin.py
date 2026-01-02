from django.contrib import admin
from .models import Bill, BillItem, Customer

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['bill_number', 'customer_name', 'total', 'payment_type', 'date', 'shop']
    list_filter = ['payment_type', 'shop', 'date']
    search_fields = ['bill_number', 'customer_name', 'customer_phone']
    readonly_fields = ['bill_number', 'date']

@admin.register(BillItem)
class BillItemAdmin(admin.ModelAdmin):
    list_display = ['bill', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['bill__shop']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'shop', 'created_at']
    list_filter = ['shop', 'created_at']
    search_fields = ['name', 'phone', 'email']
