from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from products.models import Product
from .models import Cart, CartItem
from decimal import Decimal

@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.filter(saved_for_later=False).select_related("product").prefetch_related("product__images")
    saved_items = cart.items.filter(saved_for_later=True).select_related("product").prefetch_related("product__images")

    from django.conf import settings
    gst = round(cart.subtotal * Decimal(str(settings.GST_PERCENT)) / 100, 2)
    shipping = Decimal("0") if cart.subtotal >= Decimal(str(settings.FREE_SHIPPING_THRESHOLD)) or cart.subtotal == 0 else Decimal(str(settings.STANDARD_SHIPPING_CHARGE))
    grand_total = cart.subtotal + gst + shipping

    return render(request, "cart/cart_detail.html", {
        "cart": cart, "items": items, "saved_items": saved_items,
        "gst": gst, "shipping": shipping, "grand_total": grand_total,
    })


@login_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
    item.saved_for_later = False
    item.save()
    messages.success(request, f"{product.name} added to cart.")
    return redirect(request.META.get("HTTP_REFERER", "cart:cart_detail"))


@login_required
@require_POST
def cart_update(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get("quantity", 1))
    if quantity < 1:
        item.delete()
    else:
        item.quantity = min(quantity, item.product.stock if item.product.stock else 0)
        item.save()
    return redirect("cart:cart_detail")


@login_required
@require_POST
def cart_remove(request, item_id):
    CartItem.objects.filter(id=item_id, cart__user=request.user).delete()
    messages.info(request, "Item removed from cart.")
    return redirect("cart:cart_detail")


@login_required
@require_POST
def cart_save_for_later(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.saved_for_later = True
    item.save()
    messages.info(request, f"{item.product.name} saved for later.")
    return redirect("cart:cart_detail")


@login_required
@require_POST
def cart_move_to_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.saved_for_later = False
    item.save()
    messages.success(request, f"{item.product.name} moved back to cart.")
    return redirect("cart:cart_detail")

@login_required
@require_POST
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if not product.in_stock:
        messages.error(request, "This product is out of stock.")
        return redirect(request.META.get("HTTP_REFERER", "products:product_list"))

    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
    item.saved_for_later = False
    item.save()
    return redirect("orders:checkout")