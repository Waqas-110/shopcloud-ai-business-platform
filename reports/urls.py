from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),

    path('sales/', views.sales_report, name='sales_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('profit/', views.profit_report, name='profit_report'),
    path('products/', views.products_report, name='products_report'),
    path('api/sales-data/', views.sales_data_api, name='sales_data'),
    path('api/sales-chart/', views.sales_chart_data, name='sales_chart_data'),
    path('api/category-sales/', views.category_sales_data, name='category_sales_data'),
    path('api/payment-methods/', views.payment_methods_data, name='payment_methods_data'),
    path('api/hourly-sales/', views.hourly_sales_data, name='hourly_sales_data'),
    path('advanced-analytics/', views.advanced_sales_analytics, name='advanced_analytics'),
    path('financial-dashboard/', views.financial_dashboard, name='financial_dashboard'),
    path('customer-analytics/', views.customer_analytics, name='customer_analytics'),
]