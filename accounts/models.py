import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Custom user model. Email is the primary identifier for login."""

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification_tokens")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and (timezone.now() - self.created_at).total_seconds() < 60 * 60 * 24

    def __str__(self):
        return f"Verification token for {self.user.email}"


class OTP(models.Model):
    PURPOSE_CHOICES = [("login", "Login"), ("password_reset", "Password Reset")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default="login")
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and (timezone.now() - self.created_at).total_seconds() < 60 * 10

    def __str__(self):
        return f"OTP({self.purpose}) for {self.user.email}"


class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [("home", "Home"), ("work", "Work"), ("other", "Other")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default="India")
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default="home")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ["-is_default", "-created_at"]

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.city} ({self.address_type})"


class SavedCard(models.Model):
    """Stores only a tokenized reference from the payment gateway — never raw card data (PCI-DSS)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_cards")
    gateway_token = models.CharField(max_length=255)
    card_brand = models.CharField(max_length=30, blank=True)
    last4 = models.CharField(max_length=4)
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.card_brand} ****{self.last4}"


class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="active_sessions")
    session_key = models.CharField(max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    last_activity = models.DateTimeField(default=timezone.now)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-last_activity"]

    def __str__(self):
        return f"Session for {self.user.email} at {self.last_activity}"
