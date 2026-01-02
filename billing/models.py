from django.db import models
from django.core.validators import MinValueValidator
from users.models import Shop
from products.models import Product
from django.utils import timezone

class Bill(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('online', 'Online'),
        ('udhaar', 'Udhaar'),
    ]
    
    bill_number = models.CharField(max_length=20, unique=True, db_index=True)
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-date']
    
    def save(self, *args, **kwargs):
        if not self.bill_number:
            today = timezone.now().strftime('%Y%m%d')
            last_bill = Bill.objects.filter(
                shop=self.shop,
                bill_number__startswith=f"{self.shop.id}{today}"
            ).order_by('-bill_number').first()
            
            if last_bill:
                last_num = int(last_bill.bill_number[-3:])
                new_num = str(last_num + 1).zfill(3)
            else:
                new_num = '001'
            
            self.bill_number = f"{self.shop.id}{today}{new_num}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Bill #{self.bill_number} - {self.shop.name}"

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.001)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name