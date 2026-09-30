from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("update/<int:item_id>/", views.cart_update, name="cart_update"),
    path("remove/<int:item_id>/", views.cart_remove, name="cart_remove"),
    path("save-for-later/<int:item_id>/", views.cart_save_for_later, name="cart_save_for_later"),
    path("move-to-cart/<int:item_id>/", views.cart_move_to_cart, name="cart_move_to_cart"),
    path("buy-now/<int:product_id>/", views.buy_now, name="buy_now"),
]
