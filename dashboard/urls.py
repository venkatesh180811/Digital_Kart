from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("seller/register/", views.seller_register, name="seller_register"),
    path("seller/", views.seller_dashboard, name="seller_dashboard"),
]
