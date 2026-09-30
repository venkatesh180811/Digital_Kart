from django.contrib import admin
from .models import SellerProfile


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "user", "status", "applied_at")
    list_filter = ("status",)
    list_editable = ("status",)
