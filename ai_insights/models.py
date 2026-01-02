from django.db import models
from users.models import Shop
from products.models import Product

class AIInsight(models.Model):
    INSIGHT_TYPES = [
        ('sales_prediction', 'Sales Prediction'),
        ('stock_alert', 'Stock Alert'),
        ('price_recommendation', 'Price Recommendation'),
        ('sales_tip', 'Sales Improvement Tip'),
        ('customer_behavior', 'Customer Behavior'),
        ('product_analysis', 'Product Analysis'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    is_read = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.shop.name}"

class SalesPrediction(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    prediction_date = models.DateField()
    predicted_sales = models.DecimalField(max_digits=10, decimal_places=2)
    predicted_quantity = models.IntegerField()
    confidence_score = models.FloatField()  # 0-1 scale
    actual_sales = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_quantity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        product_name = self.product.name if self.product else "Overall"
        return f"{product_name} - {self.prediction_date}"

class StockPrediction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    predicted_stock_out_date = models.DateField()
    recommended_reorder_quantity = models.IntegerField()
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} - Stock out: {self.predicted_stock_out_date}"

class PriceRecommendation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    recommended_price = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    expected_impact = models.CharField(max_length=200)
    confidence_score = models.FloatField()
    is_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} - ₨{self.current_price} → ₨{self.recommended_price}"