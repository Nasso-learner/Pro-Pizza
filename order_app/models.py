from django.db import models

# Create your models here.
from django.db import models

class Pizza(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("IN_PROGRESS", "In Progress"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    customer_name = models.CharField(max_length=100)
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"




class DeliveryBoy(models.Model):
    keycloak_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    current_location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class Delivery(models.Model):
    STATUS_CHOICES = [
        ("ASSIGNED", "Assigned"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("FAILED", "Failed"),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    delivery_boy = models.ForeignKey(DeliveryBoy, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ASSIGNED")
    delivery_location = models.CharField(max_length=255)
    delivered_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Delivery for Order #{self.order.id}"