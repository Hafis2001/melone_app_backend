from django.db import models
import uuid

def generate_shop_code():
    return uuid.uuid4().hex[:6].upper()
class Owner(models.Model):
    name = models.CharField(max_length=255)
    shop_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255) # Stored as bcrypt hash
    shop_code = models.CharField(max_length=10, null=True, blank=True, unique=True, default=generate_shop_code)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.shop_name}"

class Staff(models.Model):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="staff")
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255) # Stored as bcrypt hash
    device_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['owner', 'username']

    def __str__(self):
        return f"{self.name} ({self.username})"

class Order(models.Model):
    order_id = models.CharField(max_length=255)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name="orders")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    items = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField()
    synced_at = models.DateTimeField(auto_now=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ['order_id', 'staff']

    def __str__(self):
        return f"Order {self.order_id} - Total: {self.total}"
