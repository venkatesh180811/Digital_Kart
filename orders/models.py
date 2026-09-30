import uuid
from django.conf import settings
from django.db import models
from products.models import Product
from accounts.models import Address


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("returned", "Returned"),
        ("refunded", "Refunded"),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(Address, on_delete=models.PROTECT)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)

    coupon_code = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=[("cod", "Cash on Delivery"), ("razorpay", "Razorpay"), ("stripe", "Stripe")])
    is_paid = models.BooleanField(default=False)

    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-placed_at"]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"DK{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def line_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    status = models.CharField(max_length=20)
    note = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["changed_at"]


class ReturnRequest(models.Model):
    REASON_CHOICES = [("defective", "Defective"), ("wrong_item", "Wrong Item"), ("not_needed", "No Longer Needed"), ("other", "Other")]
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="return_requests")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    comments = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[("requested", "Requested"), ("approved", "Approved"), ("rejected", "Rejected"), ("refunded", "Refunded")], default="requested")
    requested_at = models.DateTimeField(auto_now_add=True)
