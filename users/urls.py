from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('shop-setup/', views.shop_setup_view, name='shop_setup'),
    path('profile/', views.profile_view, name='profile'),
    path('admin/accounts/', views.admin_accounts_management, name='admin_accounts'),
]