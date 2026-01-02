from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.main_dashboard, name='main'),
    path('reports/', views.reports_dashboard, name='reports'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('api/chart-data/', views.chart_data_api, name='chart_data_api'),
    path('export/sales-report/', views.export_sales_report, name='export_sales_report'),
]