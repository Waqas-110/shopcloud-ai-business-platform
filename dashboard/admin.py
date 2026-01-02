from django.contrib import admin
from .models import SalesAnalytics, ProductSalesReport, CategorySalesReport

@admin.register(SalesAnalytics)
class SalesAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'shop', 'total_sales', 'total_bills', 'total_profit']
    list_filter = ['shop', 'date']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'

@admin.register(ProductSalesReport)
class ProductSalesReportAdmin(admin.ModelAdmin):
    list_display = ['product', 'date', 'quantity_sold', 'total_revenue', 'total_profit', 'shop']
    list_filter = ['shop', 'date', 'product__category']
    search_fields = ['product__name']
    date_hierarchy = 'date'

@admin.register(CategorySalesReport)
class CategorySalesReportAdmin(admin.ModelAdmin):
    list_display = ['category', 'date', 'total_revenue', 'total_profit', 'items_sold', 'shop']
    list_filter = ['shop', 'date']
    date_hierarchy = 'date'
