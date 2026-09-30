from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, ReturnRequest


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "grand_total", "status", "payment_method", "is_paid", "placed_at")
    list_filter = ("status", "payment_method", "is_paid")
    search_fields = ("order_number", "user__email")
    inlines = [OrderItemInline]
    list_editable = ("status",)


admin.site.register(OrderStatusHistory)
admin.site.register(ReturnRequest)
