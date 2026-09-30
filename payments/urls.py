from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("<int:order_id>/start/", views.payment_start, name="payment_start"),
    path("<int:order_id>/success/", views.payment_success, name="payment_success"),
    path("<int:order_id>/failure/", views.payment_failure, name="payment_failure"),
    path("<int:order_id>/razorpay/callback/", views.razorpay_callback, name="razorpay_callback"),
    path("<int:order_id>/razorpay/webhook/", views.razorpay_webhook, name="razorpay_webhook"),
    path("<int:order_id>/stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]
