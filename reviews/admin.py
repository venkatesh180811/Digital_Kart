from django.contrib import admin
from .models import Review, ReviewImage


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_verified_purchase", "created_at")
    list_filter = ("rating", "is_verified_purchase")


admin.site.register(ReviewImage)
