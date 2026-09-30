from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from accounts.models import Address
from cart.models import Cart, CartItem
from .models import Order, OrderItem, OrderStatusHistory, ReturnRequest


@login_required
def checkout_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.filter(saved_for_later=False).select_related("product")
    if not items:
        messages.warning(request, "Your cart is empty.")
        return redirect("cart:cart_detail")

    addresses = request.user.addresses.all()
    gst = round(cart.subtotal * Decimal(str(settings.GST_PERCENT)) / 100, 2)
    free_shipping_threshold = Decimal(str(settings.FREE_SHIPPING_THRESHOLD))
    shipping = Decimal("0") if cart.subtotal >= free_shipping_threshold else Decimal(str(settings.STANDARD_SHIPPING_CHARGE))
    grand_total = cart.subtotal + gst + shipping

    if request.method == "POST":
        address_id = request.POST.get("address_id")
        payment_method = request.POST.get("payment_method", "cod")

        if not address_id:
            messages.error(request, "Please add and select a delivery address before placing your order.")
            if not addresses:
                return redirect("accounts:address_add")
            return redirect("orders:checkout")

        address = Address.objects.filter(id=address_id, user=request.user).first()
        if address is None:
            messages.error(request, "That address could not be found. Please select a valid delivery address.")
            return redirect("orders:checkout")

        order = Order.objects.create(
            user=request.user, address=address,
            subtotal=cart.subtotal, gst_amount=gst, shipping_charge=shipping,
            grand_total=grand_total, payment_method=payment_method,
            is_paid=(payment_method != "cod"),
        )
        for item in items:
            OrderItem.objects.create(order=order, product=item.product, product_name=item.product.name, price=item.product.price, quantity=item.quantity)
            item.product.stock = max(item.product.stock - item.quantity, 0)
            item.product.save(update_fields=["stock"])
        OrderStatusHistory.objects.create(order=order, status="pending", note="Order placed")
        items.delete()

        if payment_method == "cod":
            messages.success(request, f"Order {order.order_number} placed successfully!")
            return redirect("orders:order_detail", order.id)
        return redirect("payments:payment_start", order.id)

    return render(request, "orders/checkout.html", {
        "items": items, "addresses": addresses, "gst": gst, "shipping": shipping, "grand_total": grand_total,
    })


@login_required
def order_list(request):
    orders = request.user.orders.all().prefetch_related("items__product__images", "history", "payment")

    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    sort = request.GET.get("sort", "newest")

    if query:
        orders = orders.filter(
            order_number__icontains=query,
            items__product_name__icontains=query,
        ).distinct()

    if status_filter:
        orders = orders.filter(status=status_filter)

    sort_map = {
        "newest": "-placed_at",
        "oldest": "placed_at",
        "amount_high": "-grand_total",
        "amount_low": "grand_total",
    }
    if sort in sort_map:
        orders = orders.order_by(sort_map[sort])
    else:
        orders = orders.order_by("-placed_at")

    paginator = Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "orders/order_list.html", {
        "page_obj": page_obj,
        "order_count": orders.count(),
        "query": query,
        "status_filter": status_filter,
        "sort": sort,
        "order_status_choices": Order.STATUS_CHOICES,
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("address", "user").prefetch_related(
            "items__product__images",
            "items__product__brand",
            "history",
            "payment",
        ),
        id=order_id,
        user=request.user,
    )
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
@require_POST
def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status in ("pending", "confirmed"):
        order.status = "cancelled"
        order.save(update_fields=["status"])
        OrderStatusHistory.objects.create(order=order, status="cancelled", note="Cancelled by customer")
        messages.success(request, "Order cancelled.")
    else:
        messages.error(request, "This order can no longer be cancelled.")
    return redirect("orders:order_detail", order.id)


@login_required
@require_POST
def order_return_request(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    ReturnRequest.objects.create(order_item=item, reason=request.POST.get("reason"), comments=request.POST.get("comments", ""))
    messages.success(request, "Return request submitted.")
    return redirect("orders:order_detail", item.order.id)


@login_required
@require_POST
def buy_again(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    added = 0
    for item in order.items.all():
        if item.product and item.product.is_active:
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, product=item.product,
                defaults={"quantity": item.quantity},
            )
            if not created:
                cart_item.quantity = max(cart_item.quantity, item.quantity)
                cart_item.save(update_fields=["quantity"])
            added += 1
    if added:
        messages.success(request, f"{added} item(s) added to cart.")
    else:
        messages.info(request, "No active products found in this order to add to cart.")
    return redirect("orders:order_list")