import os
import json
import re
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.utils import timezone

from products.models import Product, ProductImage, Category, Brand
from orders.models import Order, OrderItem, OrderStatusHistory
from cart.models import Cart, CartItem
from wishlist.models import WishlistItem
from reviews.models import Review

User = get_user_model()


def search_products(query="", category=None, brand=None, min_price=None, max_price=None, limit=8):
    qs = Product.objects.filter(is_active=True).select_related("category", "brand").prefetch_related("images")

    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(specifications__icontains=query)
            | Q(brand__name__icontains=query)
        )
    if category:
        qs = qs.filter(category__slug=category)
    if brand:
        qs = qs.filter(brand__slug=brand)
    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)

    qs = qs.annotate(review_count_=Count("reviews"), avg_rating_=Avg("reviews__rating"))
    qs = qs.order_by("-created_at")[:limit]

    results = []
    for p in qs:
        img_url = ""
        primary = p.images.filter(is_primary=True).first()
        if not primary:
            primary = p.images.first()
        if primary:
            img_url = primary.image.url

        results.append({
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "price": float(p.price),
            "mrp": float(p.mrp) if p.mrp else None,
            "discount_percent": p.discount_percent,
            "brand": p.brand.name if p.brand else "",
            "category": p.category.name if p.category else "",
            "image": img_url,
            "url": p.get_absolute_url(),
            "stock": p.stock,
            "in_stock": p.in_stock,
            "average_rating": round(p.avg_rating_, 1) if p.avg_rating_ else 0,
            "review_count": p.review_count_ or 0,
        })
    return results


def get_product_details(product_id):
    try:
        p = Product.objects.select_related("category", "brand").prefetch_related("images").get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return None

    img_url = ""
    primary = p.images.filter(is_primary=True).first()
    if not primary:
        primary = p.images.first()
    if primary:
        img_url = primary.image.url

    return {
        "id": p.id,
        "name": p.name,
        "slug": p.slug,
        "price": float(p.price),
        "mrp": float(p.mrp) if p.mrp else None,
        "discount_percent": p.discount_percent,
        "brand": p.brand.name if p.brand else "",
        "category": p.category.name if p.category else "",
        "image": img_url,
        "url": p.get_absolute_url(),
        "stock": p.stock,
        "in_stock": p.in_stock,
        "description": p.description[:300] if p.description else "",
        "specifications": p.specifications or {},
    }


def get_user_orders(user, limit=5):
    if not user.is_authenticated:
        return []
    orders = (
        Order.objects.filter(user=user)
        .prefetch_related("items__product__images", "history")
        .order_by("-placed_at")[:limit]
    )
    result = []
    for o in orders:
        items = []
        for item in o.items.all():
            img_url = ""
            if item.product:
                primary = item.product.images.filter(is_primary=True).first()
                if not primary:
                    primary = item.product.images.first()
                if primary:
                    img_url = primary.image.url
            items.append({
                "id": item.id,
                "product_name": item.product_name,
                "price": float(item.price),
                "quantity": item.quantity,
                "line_total": float(item.line_total),
                "image": img_url,
                "product_url": item.product.get_absolute_url() if item.product else None,
                "product_exists": item.product is not None,
            })
        result.append({
            "id": o.id,
            "order_number": o.order_number,
            "status": o.status,
            "status_display": o.get_status_display(),
            "placed_at": o.placed_at.strftime("%d %b %Y, %I:%M %p"),
            "grand_total": float(o.grand_total),
            "payment_method": o.get_payment_method_display(),
            "is_paid": o.is_paid,
            "items": items,
            "url": f"/orders/{o.id}/",
        })
    return result


def get_order_details(order_id, user):
    try:
        o = Order.objects.select_related("address", "user").prefetch_related("items__product__images", "history").get(id=order_id, user=user)
    except Order.DoesNotExist:
        return None

    items = []
    for item in o.items.all():
        img_url = ""
        if item.product:
            primary = item.product.images.filter(is_primary=True).first()
            if not primary:
                primary = item.product.images.first()
            if primary:
                img_url = primary.image.url
        items.append({
            "id": item.id,
            "product_name": item.product_name,
            "price": float(item.price),
            "quantity": item.quantity,
            "line_total": float(item.line_total),
            "image": img_url,
            "product_url": item.product.get_absolute_url() if item.product else None,
            "product_exists": item.product is not None,
        })

    history = []
    for h in o.history.all():
        history.append({
            "status": h.status,
            "note": h.note,
            "changed_at": h.changed_at.strftime("%d %b, %I:%M %p"),
        })

    return {
        "id": o.id,
        "order_number": o.order_number,
        "status": o.status,
        "status_display": o.get_status_display(),
        "placed_at": o.placed_at.strftime("%d %b %Y, %I:%M %p"),
        "grand_total": float(o.grand_total),
        "subtotal": float(o.subtotal),
        "discount_amount": float(o.discount_amount),
        "shipping_charge": float(o.shipping_charge),
        "gst_amount": float(o.gst_amount),
        "payment_method": o.get_payment_method_display(),
        "is_paid": o.is_paid,
        "address": {
            "full_name": o.address.full_name,
            "address_line1": o.address.address_line1,
            "address_line2": o.address.address_line2 or "",
            "city": o.address.city,
            "state": o.address.state,
            "pincode": o.address.pincode,
            "phone_number": o.address.phone_number,
        },
        "items": items,
        "history": history,
        "url": f"/orders/{o.id}/",
        "can_cancel": o.status in ("pending", "confirmed"),
        "can_return": o.status == "delivered",
    }


def get_cart_summary(user):
    if not user.is_authenticated:
        return {"items": [], "total": 0, "count": 0}
    cart, _ = Cart.objects.get_or_create(user=user)
    items = []
    total = 0
    count = 0
    for ci in cart.items.filter(saved_for_later=False).select_related("product__images"):
        img_url = ""
        primary = ci.product.images.filter(is_primary=True).first()
        if not primary:
            primary = ci.product.images.first()
        if primary:
            img_url = primary.image.url
        line = float(ci.line_total)
        total += line
        count += ci.quantity
        items.append({
            "id": ci.id,
            "product_id": ci.product.id,
            "name": ci.product.name,
            "price": float(ci.product.price),
            "quantity": ci.quantity,
            "line_total": line,
            "image": img_url,
            "url": ci.product.get_absolute_url(),
        })
    return {"items": items, "total": total, "count": count}


def add_to_cart(user, product_id, quantity=1):
    if not user.is_authenticated:
        return {"success": False, "message": "Please log in to add items to cart."}
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return {"success": False, "message": "Product not found."}

    cart, _ = Cart.objects.get_or_create(user=user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": quantity})
    if not created:
        item.quantity = max(item.quantity, quantity)
        item.save(update_fields=["quantity"])
    return {"success": True, "message": f"Added {quantity} x {product.name} to cart.", "cart_count": cart.total_items}


def remove_from_cart(user, product_id):
    if not user.is_authenticated:
        return {"success": False, "message": "Please log in to modify your cart."}
    try:
        cart = Cart.objects.get(user=user)
        item = cart.items.get(product_id=product_id)
        item.delete()
        return {"success": True, "message": "Item removed from cart.", "cart_count": cart.total_items}
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        return {"success": False, "message": "Item not found in cart."}


def get_wishlist_summary(user):
    if not user.is_authenticated:
        return {"items": [], "count": 0}
    items = []
    for wi in WishlistItem.objects.filter(user=user).select_related("product__images"):
        img_url = ""
        primary = wi.product.images.filter(is_primary=True).first()
        if not primary:
            primary = wi.product.images.first()
        if primary:
            img_url = primary.image.url
        items.append({
            "id": wi.id,
            "product_id": wi.product.id,
            "name": wi.product.name,
            "price": float(wi.product.price),
            "image": img_url,
            "url": wi.product.get_absolute_url(),
        })
    return {"items": items, "count": len(items)}


def add_to_wishlist(user, product_id):
    if not user.is_authenticated:
        return {"success": False, "message": "Please log in to use wishlist."}
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return {"success": False, "message": "Product not found."}
    _, created = WishlistItem.objects.get_or_create(user=user, product=product)
    if created:
        return {"success": True, "message": f"Added {product.name} to wishlist."}
    return {"success": True, "message": "This product is already in your wishlist."}


def remove_from_wishlist(user, product_id):
    if not user.is_authenticated:
        return {"success": False, "message": "Please log in to modify your wishlist."}
    try:
        wi = WishlistItem.objects.get(user=user, product_id=product_id)
        wi.delete()
        return {"success": True, "message": "Removed from wishlist."}
    except WishlistItem.DoesNotExist:
        return {"success": False, "message": "Item not found in wishlist."}


def cancel_order(user, order_id):
    if not user.is_authenticated:
        return {"success": False, "message": "Please log in to cancel orders."}
    try:
        order = Order.objects.get(id=order_id, user=user)
    except Order.DoesNotExist:
        return {"success": False, "message": "Order not found."}
    if order.status not in ("pending", "confirmed"):
        return {"success": False, "message": "This order can no longer be cancelled."}
    order.status = "cancelled"
    order.save(update_fields=["status"])
    OrderStatusHistory.objects.create(order=order, status="cancelled", note="Cancelled via chatbot")
    return {"success": True, "message": f"Order {order.order_number} has been cancelled."}


def create_return_request(user, order_item_id, reason, comments=""):
    if not user.is_authenticated:
        return {"success": False, "message": "Please log in to request a return."}
    try:
        item = OrderItem.objects.get(id=order_item_id, order__user=user)
    except OrderItem.DoesNotExist:
        return {"success": False, "message": "Order item not found."}
    if item.order.status != "delivered":
        return {"success": False, "message": "Only delivered orders can be returned."}
    ReturnRequest.objects.create(order_item=item, reason=reason, comments=comments)
    return {"success": True, "message": "Return request submitted successfully."}


TOOL_REGISTRY = {
    "search_products": {
        "name": "Search Products",
        "description": "Search DigitalKart products by name, category, brand, or price range.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "category": {"type": "string", "description": "Category slug"},
                "brand": {"type": "string", "description": "Brand slug"},
                "min_price": {"type": "number", "description": "Minimum price"},
                "max_price": {"type": "number", "description": "Maximum price"},
                "limit": {"type": "integer", "description": "Max results"},
            },
        },
    },
    "get_product_details": {
        "name": "Product Details",
        "description": "Get detailed information about a specific product.",
        "parameters": {
            "type": "object",
            "properties": {"product_id": {"type": "integer", "description": "Product ID"}},
        },
    },
    "get_user_orders": {
        "name": "My Orders",
        "description": "Get the authenticated user's recent orders.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "Max orders"}},
        },
    },
    "get_order_details": {
        "name": "Order Details",
        "description": "Get full details of a specific order.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "integer", "description": "Order ID"}},
        },
    },
    "get_cart_summary": {
        "name": "Cart Summary",
        "description": "Get current cart contents and total.",
        "parameters": {"type": "object", "properties": {}},
    },
    "add_to_cart": {
        "name": "Add to Cart",
        "description": "Add a product to the user's cart.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer", "description": "Product ID"},
                "quantity": {"type": "integer", "description": "Quantity"},
            },
        },
    },
    "remove_from_cart": {
        "name": "Remove from Cart",
        "description": "Remove a product from the user's cart.",
        "parameters": {
            "type": "object",
            "properties": {"product_id": {"type": "integer", "description": "Product ID"}},
        },
    },
    "get_wishlist_summary": {
        "name": "Wishlist Summary",
        "description": "Get current wishlist contents.",
        "parameters": {"type": "object", "properties": {}},
    },
    "add_to_wishlist": {
        "name": "Add to Wishlist",
        "description": "Add a product to the user's wishlist.",
        "parameters": {
            "type": "object",
            "properties": {"product_id": {"type": "integer", "description": "Product ID"}},
        },
    },
    "remove_from_wishlist": {
        "name": "Remove from Wishlist",
        "description": "Remove a product from the user's wishlist.",
        "parameters": {
            "type": "object",
            "properties": {"product_id": {"type": "integer", "description": "Product ID"}},
        },
    },
    "cancel_order": {
        "name": "Cancel Order",
        "description": "Cancel an order if eligible.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "integer", "description": "Order ID"}},
        },
    },
    "create_return_request": {
        "name": "Create Return Request",
        "description": "Create a return request for an order item.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_item_id": {"type": "integer", "description": "Order Item ID"},
                "reason": {"type": "string", "description": "Return reason"},
                "comments": {"type": "string", "description": "Additional comments"},
            },
        },
    },
}


def execute_tool(tool_name, arguments, user):
    if tool_name == "search_products":
        return search_products(**arguments)
    if tool_name == "get_product_details":
        return get_product_details(**arguments)
    if tool_name == "get_user_orders":
        return get_user_orders(user, **arguments)
    if tool_name == "get_order_details":
        order_id = arguments.get("order_id")
        return get_order_details(order_id, user)
    if tool_name == "get_cart_summary":
        return get_cart_summary(user)
    if tool_name == "add_to_cart":
        return add_to_cart(user, **arguments)
    if tool_name == "remove_from_cart":
        return remove_from_cart(user, **arguments)
    if tool_name == "get_wishlist_summary":
        return get_wishlist_summary(user)
    if tool_name == "add_to_wishlist":
        return add_to_wishlist(user, **arguments)
    if tool_name == "remove_from_wishlist":
        return remove_from_wishlist(user, **arguments)
    if tool_name == "cancel_order":
        return cancel_order(user, **arguments)
    if tool_name == "create_return_request":
        return create_return_request(user, **arguments)
    return {"error": f"Unknown tool: {tool_name}"}


def build_system_prompt():
    return (
        "You are DigitalKart AI Customer Support Assistant.\n\n"
        "You help customers with:\n"
        "- Product discovery and recommendations\n"
        "- Product information (price, stock, specs)\n"
        "- Order tracking and status\n"
        "- Delivery information\n"
        "- Returns and replacements\n"
        "- Order cancellations\n"
        "- Cart and wishlist assistance\n"
        "- General DigitalKart support\n\n"
        "Always use the provided tools to fetch real data from DigitalKart systems. "
        "Never invent products, prices, order statuses, delivery dates, or policies. "
        "If required information is unavailable, clearly tell the user.\n\n"
        "For actions that change user data or orders (cancel, return, add to cart, etc.), "
        "ask for confirmation before performing the action.\n\n"
        "Be concise, friendly, helpful and professional."
    )
