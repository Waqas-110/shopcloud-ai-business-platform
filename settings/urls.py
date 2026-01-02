from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('shop/', views.shop_settings, name='shop_settings'),
    path('password/', views.change_password, name='change_password'),
    path('preferences/', views.preferences, name='preferences'),
    path('payment-options/', views.payment_options, name='payment_options'),
    path('data-backup/', views.data_backup, name='data_backup'),
    path('export-data/', views.export_data, name='export_data'),
]