from django.contrib import admin
from .models import AIInsight, SalesPrediction, StockPrediction, PriceRecommendation

@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'insight_type', 'priority', 'shop', 'is_read', 'created_at']
    list_filter = ['insight_type', 'priority', 'is_read', 'shop', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(SalesPrediction)
class SalesPredictionAdmin(admin.ModelAdmin):
    list_display = ['shop', 'product', 'prediction_date', 'predicted_sales', 'confidence_score']
    list_filter = ['shop', 'prediction_date']
    readonly_fields = ['created_at']

@admin.register(StockPrediction)
class StockPredictionAdmin(admin.ModelAdmin):
    list_display = ['product', 'predicted_stock_out_date', 'recommended_reorder_quantity', 'confidence_score']
    list_filter = ['predicted_stock_out_date']
    readonly_fields = ['created_at']

@admin.register(PriceRecommendation)
class PriceRecommendationAdmin(admin.ModelAdmin):
    list_display = ['product', 'current_price', 'recommended_price', 'is_applied', 'confidence_score']
    list_filter = ['is_applied', 'created_at']
    readonly_fields = ['created_at']
