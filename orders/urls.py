from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout_view, name="checkout"),
    path("", views.order_list, name="order_list"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
    path("<int:order_id>/cancel/", views.order_cancel, name="order_cancel"),
    path("<int:order_id>/buy-again/", views.buy_again, name="buy_again"),
    path("item/<int:item_id>/return/", views.order_return_request, name="order_return_request"),
]
