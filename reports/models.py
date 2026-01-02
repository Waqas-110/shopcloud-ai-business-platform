from django.db import models
from users.models import Shop

class ReportTemplate(models.Model):
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('profit', 'Profit & Loss Report'),
        ('customer', 'Customer Report'),
        ('payment', 'Payment Method Report'),
    ]
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.shop.name}"