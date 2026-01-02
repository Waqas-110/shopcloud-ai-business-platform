from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Products
    path('', views.product_list, name='list'),
    path('add/', views.add_product, name='add'),
    path('edit/<int:product_id>/', views.edit_product, name='edit'),
    path('delete/<int:product_id>/', views.delete_product, name='delete'),
    
    # Categories
    path('categories/', views.category_list, name='categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    
    # Bulk Operations
    path('export/', views.export_products, name='export'),
    path('import/', views.import_products, name='import'),
    path('generate-barcode/', views.generate_barcode, name='generate_barcode'),
    path('bulk-update-stock/', views.bulk_update_stock, name='bulk_update_stock'),
    path('low-stock-alert/', views.low_stock_alert, name='low_stock_alert'),
]