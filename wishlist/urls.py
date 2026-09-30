from django.urls import path
from . import views

app_name = "wishlist"

urlpatterns = [
    path("", views.wishlist_view, name="wishlist"),
    path("add/<int:product_id>/", views.wishlist_add, name="wishlist_add"),
    path("remove/<int:product_id>/", views.wishlist_remove, name="wishlist_remove"),
    path("move-to-cart/<int:product_id>/", views.wishlist_move_to_cart, name="wishlist_move_to_cart"),
]
