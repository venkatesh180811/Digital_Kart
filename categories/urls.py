from django.urls import path
from . import views

app_name = "categories"

urlpatterns = [
    path("<slug:slug>/", views.category_detail, name="category_detail"),
]
