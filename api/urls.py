from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Product APIs
    path('products/', views.products_api, name='products'),
    path('products/create/', views.create_product_api, name='create_product'),
    path('products/<int:product_id>/update/', views.update_product_api, name='update_product'),
    path('products/bulk-update-stock/', views.bulk_update_stock_api, name='bulk_update_stock'),
    path('products/low-stock/', views.low_stock_products_api, name='low_stock_products'),
    
    # Billing APIs
    path('bills/create/', views.create_bill_api, name='create_bill'),
    path('sales/summary/', views.sales_summary_api, name='sales_summary'),
    
    # Dashboard APIs
    path('dashboard/stats/', views.dashboard_stats_api, name='dashboard_stats'),
]