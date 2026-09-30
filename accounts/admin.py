from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, EmailVerificationToken, OTP, SavedCard


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "phone_number", "is_seller", "is_email_verified", "is_staff", "date_joined")
    list_filter = ("is_seller", "is_email_verified", "is_staff", "is_active")
    search_fields = ("email", "username", "phone_number")
    ordering = ("-date_joined",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("DigitalKart Profile", {"fields": ("phone_number", "profile_picture", "is_email_verified", "is_seller")}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "city", "state", "address_type", "is_default")
    list_filter = ("address_type", "is_default", "state")
    search_fields = ("full_name", "user__email", "city", "pincode")


admin.site.register(EmailVerificationToken)
admin.site.register(OTP)
admin.site.register(SavedCard)

admin.site.site_header = "DigitalKart Administration"
admin.site.site_title = "DigitalKart Admin"
admin.site.index_title = "Manage your store"
