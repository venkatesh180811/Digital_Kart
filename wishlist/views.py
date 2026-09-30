from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from products.models import Product
from cart.models import Cart, CartItem
from .models import WishlistItem


@login_required
def wishlist_view(request):
    items = WishlistItem.objects.filter(user=request.user).select_related("product")
    return render(request, "wishlist/wishlist.html", {"items": items})


@login_required
@require_POST
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    _, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    msg = "Added to wishlist." if created else "Already in your wishlist."

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "status": "ok",
            "created": created,
            "message": msg,
            "in_wishlist": True,
        })
    messages.success(request, msg)
    return redirect(request.META.get("HTTP_REFERER", "wishlist:wishlist"))


@login_required
@require_POST
def wishlist_remove(request, product_id):
    WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "status": "ok",
            "message": "Removed from wishlist.",
            "in_wishlist": False,
        })
    messages.info(request, "Removed from wishlist.")
    return redirect("wishlist:wishlist")


@login_required
@require_POST
def wishlist_move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    WishlistItem.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f"{product.name} moved to cart.")
    return redirect("wishlist:wishlist")
