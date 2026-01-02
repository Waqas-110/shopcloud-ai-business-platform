from django.db import models
from users.models import Shop
from products.models import Product, Category
from django.utils import timezone

class SalesAnalytics(models.Model):
    date = models.DateField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_bills = models.IntegerField(default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date', 'shop']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.shop.name} - {self.date} - Rs.{self.total_sales}"

class ProductSalesReport(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date = models.DateField()
    quantity_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['product', 'date', 'shop']
        ordering = ['-date', '-quantity_sold']
    
    def __str__(self):
        return f"{self.product.name} - {self.date} - {self.quantity_sold} sold"

class CategorySalesReport(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateField()
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    items_sold = models.IntegerField(default=0)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['category', 'date', 'shop']
        ordering = ['-date', '-total_revenue']
    
    def __str__(self):
        return f"{self.category.name} - {self.date} - Rs.{self.total_revenue}"