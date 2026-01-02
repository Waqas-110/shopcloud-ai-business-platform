from django.db import models
from django.contrib.auth.models import User

class Shop(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    whatsapp = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='shop_logos/', blank=True, null=True)
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name