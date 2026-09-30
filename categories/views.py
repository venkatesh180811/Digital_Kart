from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Min, Max, F
from .models import Category
from products.models import Product, Brand
from wishlist.models import WishlistItem


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True).select_related("brand").annotate(
        rating_avg=Avg("reviews__rating"),
        total_reviews=Count("reviews"),
    )

    brand_slug = request.GET.get("brand")
    if brand_slug:
        products = products.filter(brand__slug=brand_slug)

    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass

    min_rating = request.GET.get("rating")
    if min_rating:
        try:
            products = products.filter(rating_avg__gte=float(min_rating))
        except (ValueError, TypeError):
            pass

    in_stock = request.GET.get("in_stock")
    if in_stock == "1":
        products = products.filter(stock__gt=0)

    discount = request.GET.get("discount")
    if discount:
        try:
            products = products.filter(mrp__gt=0)
            products = products.annotate(
                discount_value=(F("mrp") - F("price")) * 100 / F("mrp")
            ).filter(discount_value__gte=float(discount))
        except (ValueError, TypeError):
            pass

    sort = request.GET.get("sort")
    sort_map = {
        "price_low": "price",
        "price_high": "-price",
        "newest": "-created_at",
        "rating": "-rating_avg",
        "popularity": "-total_reviews",
        "discount": "-discount_value",
    }
    if sort in sort_map:
        products = products.order_by(sort_map[sort])
    else:
        products = products.order_by("-created_at")

    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(products__category=category).distinct()

    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True))

    active_filters = []
    if brand_slug:
        try:
            brand = Brand.objects.get(slug=brand_slug)
            active_filters.append({"type": "brand", "label": brand.name, "value": brand_slug})
        except Brand.DoesNotExist:
            pass
    if min_price or max_price:
        label = "Price: "
        if min_price and max_price:
            label += f"₹{min_price} – ₹{max_price}"
        elif min_price:
            label += f"₹{min_price}+"
        else:
            label += f"Up to ₹{max_price}"
        active_filters.append({"type": "price", "label": label, "value": {"min": min_price, "max": max_price}})
    if min_rating:
        active_filters.append({"type": "rating", "label": f"{min_rating}★ & above", "value": min_rating})
    if in_stock == "1":
        active_filters.append({"type": "in_stock", "label": "In Stock", "value": "1"})
    if discount:
        active_filters.append({"type": "discount", "label": f"{discount}%+ off", "value": discount})

    return render(request, "categories/category_detail.html", {
        "category": category,
        "page_obj": page_obj,
        "categories": categories,
        "brands": brands,
        "wishlist_ids": wishlist_ids,
        "active_filters": active_filters,
        "sort": sort,
    })
