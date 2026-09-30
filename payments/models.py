from django.db import models
from orders.models import Order


class Payment(models.Model):
    STATUS_CHOICES = [("initiated", "Initiated"), ("success", "Success"), ("failed", "Failed")]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    gateway = models.CharField(max_length=20, choices=[("cod", "COD"), ("razorpay", "Razorpay"), ("stripe", "Stripe")])
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_order_id = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="initiated")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.order.order_number} ({self.status})"
