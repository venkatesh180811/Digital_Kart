from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [("percent", "Percentage"), ("flat", "Flat Amount")]

    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default="percent")
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=100)
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def is_valid(self, order_value):
        now = timezone.now()
        return (
            self.is_active
            and self.valid_from <= now <= self.valid_until
            and self.times_used < self.usage_limit
            and order_value >= self.min_order_value
        )

    def calculate_discount(self, order_value):
        if self.discount_type == "percent":
            discount = order_value * self.discount_value / 100
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = self.discount_value
        return round(min(discount, order_value), 2)

    def __str__(self):
        return self.code
