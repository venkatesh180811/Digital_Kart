from django.conf import settings
from django.db import models


class SellerProfile(models.Model):
    STATUS_CHOICES = [("pending", "Pending Approval"), ("approved", "Approved"), ("rejected", "Rejected")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_profile")
    business_name = models.CharField(max_length=150)
    gstin = models.CharField(max_length=20, blank=True)
    business_address = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name
