from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="notification_list"),
    path("<int:pk>/delete/", views.notification_delete, name="notification_delete"),
]
