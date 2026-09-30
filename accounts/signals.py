from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_welcome_notification(sender, instance, created, **kwargs):
    if created:
        from notifications.models import Notification

        Notification.objects.create(
            user=instance,
            title="Welcome to DigitalKart!",
            message="Your account has been created. Start exploring today's best deals.",
            notification_type="account",
        )
