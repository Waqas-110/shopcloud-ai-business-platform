from django.urls import path
from . import views

app_name = 'ai_insights'

urlpatterns = [
    path('', views.ai_dashboard, name='dashboard'),
    path('ur/', views.ai_dashboard_ur, name='dashboard_ur'),
    path('ml-dashboard/', views.ml_dashboard, name='ml_dashboard'),
    path('sales-predictions/', views.sales_predictions, name='sales_predictions'),
    path('stock-predictions/', views.stock_predictions, name='stock_predictions'),
    path('price-recommendations/', views.price_recommendations, name='price_recommendations'),
    path('mark-read/<int:insight_id>/', views.mark_insight_read, name='mark_insight_read'),
    path('apply-price/', views.apply_price_recommendation, name='apply_price'),
    path('api/analytics/', views.get_analytics_data, name='analytics_api'),
    path('api/ml-analytics/', views.ml_analytics_api, name='ml_analytics_api'),
    path('refresh/', views.refresh_insights, name='refresh_insights'),
    path('train-models/', views.train_ml_models, name='train_ml_models'),
]