from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F

from products.models import Product, Brand, Category
from wishlist.models import WishlistItem


def search_view(request):
    query = request.GET.get("q", "").strip()
    results = Product.objects.filter(is_active=True).select_related("category", "brand").annotate(
        rating_avg=Avg("reviews__rating"),
        total_reviews=Count("reviews"),
    )

    if query:
        results = results.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(brand__name__icontains=query),
        )
        if request.user.is_authenticated:
            from .models import SearchHistory
            SearchHistory.objects.create(user=request.user, query=query)

    brand_slug = request.GET.get("brand")
    if brand_slug:
        results = results.filter(brand__slug=brand_slug)

    category_slug = request.GET.get("category")
    if category_slug:
        results = results.filter(category__slug=category_slug)

    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    if min_price:
        try:
            results = results.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass
    if max_price:
        try:
            results = results.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass

    min_rating = request.GET.get("rating")
    if min_rating:
        try:
            results = results.filter(rating_avg__gte=float(min_rating))
        except (ValueError, TypeError):
            pass

    in_stock = request.GET.get("in_stock")
    if in_stock == "1":
        results = results.filter(stock__gt=0)

    discount = request.GET.get("discount")
    if discount:
        try:
            results = results.filter(mrp__gt=0)
            results = results.annotate(
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
        results = results.order_by(sort_map[sort])
    else:
        results = results.order_by("-created_at")

    paginator = Paginator(results, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.all()
    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True))

    active_filters = []
    if category_slug:
        try:
            cat = Category.objects.get(slug=category_slug, is_active=True)
            active_filters.append({"type": "category", "label": cat.name, "value": category_slug})
        except Category.DoesNotExist:
            pass
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

    popular_searches = ["mobiles", "laptops", "shoes", "headphones", "watches"]
    return render(request, "search/search_results.html", {
        "query": query,
        "page_obj": page_obj,
        "categories": categories,
        "brands": brands,
        "wishlist_ids": wishlist_ids,
        "active_filters": active_filters,
        "sort": sort,
        "popular_searches": popular_searches,
    })


def search_autocomplete(request):
    query = request.GET.get("q", "").strip()
    suggestions = []
    if query:
        suggestions = list(Product.objects.filter(name__icontains=query, is_active=True).values_list("name", flat=True)[:8])
    return JsonResponse({"suggestions": suggestions})
