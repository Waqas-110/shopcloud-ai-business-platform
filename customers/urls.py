from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customers_list, name='list'),
    path('ur/', views.customers_list_ur, name='list_ur'),
    path('add/', views.add_customer, name='add'),
    path('add/ur/', views.add_customer_ur, name='add_ur'),
    path('<int:customer_id>/', views.customer_detail, name='detail'),
]