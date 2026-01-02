from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('pos/', views.pos_interface, name='pos'),
    path('search-products/', views.search_products, name='search_products'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('create-bill/', views.create_bill, name='create_bill'),
    path('bill/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('bill/<int:bill_id>/pdf/', views.bill_pdf, name='bill_pdf'),
    path('bills/', views.bills_list, name='bills_list'),
    path('history/', views.bill_history, name='bill_history'),
    path('search-customers/', views.search_customers, name='search_customers'),
]