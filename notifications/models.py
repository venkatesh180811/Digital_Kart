from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [("account", "Account"), ("order", "Order"), ("offer", "Offer"), ("stock", "Stock Alert")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="account")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
