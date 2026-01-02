from django.db import models
from django.core.validators import MinValueValidator
from users.models import Shop
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return f"{self.name} - {self.shop.name}"

class Product(models.Model):
    UNIT_CHOICES = [
        ('piece', 'Piece'),
        ('kg', 'Kilogram'),
        ('liter', 'Liter'),
        ('meter', 'Meter'),
        ('box', 'Box'),
        ('dozen', 'Dozen'),
    ]
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    min_stock_alert = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    barcode = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField(blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['barcode', 'shop']
        constraints = [
            models.UniqueConstraint(
                fields=['barcode', 'shop'],
                condition=models.Q(barcode__isnull=False),
                name='unique_barcode_per_shop'
            )
        ]
    
    def __str__(self):
        return f"{self.name} - {self.shop.name}"
    
    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = str(uuid.uuid4())[:12].upper()
        super().save(*args, **kwargs)
    
    @property
    def is_low_stock(self):
        return self.stock <= self.min_stock_alert
    
    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.sale_price - self.cost_price) / self.cost_price) * 100
        return 0