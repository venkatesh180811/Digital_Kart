from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg, Count, Min, Max, F
from .models import Product
from categories.models import Category, Brand
from wishlist.models import WishlistItem


def home(request):
    featured = Product.objects.filter(is_active=True, is_featured=True).select_related("category", "brand").prefetch_related("images")[:8]
    deals = Product.objects.filter(is_active=True).select_related("category", "brand").prefetch_related("images").order_by("-created_at")[:8]
    best_sellers = Product.objects.filter(is_active=True, is_best_seller=True).select_related("category", "brand").prefetch_related("images")[:8]
    new_arrivals = Product.objects.filter(is_active=True).select_related("category", "brand").prefetch_related("images").order_by("-created_at")[:8]
    categories = Category.objects.filter(is_active=True)[:10]
    recently_viewed = []
    wishlist_ids = set()
    if request.user.is_authenticated:
        recently_viewed = [rv.product for rv in request.user.recently_viewed.select_related("product")[:8]]
        wishlist_ids = set(WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True))
    return render(request, "products/home.html", {
        "featured": featured,
        "deals": deals,
        "best_sellers": best_sellers,
        "new_arrivals": new_arrivals,
        "categories": categories,
        "recently_viewed": recently_viewed,
        "wishlist_ids": wishlist_ids,
    })


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related("category", "brand").prefetch_related("images").annotate(
        rating_avg=Avg("reviews__rating"),
        total_reviews=Count("reviews"),
    )

    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

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
    brands = Brand.objects.all()
    price_stats = Product.objects.filter(is_active=True).aggregate(
        min_price=Min("price"), max_price=Max("price")
    )

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

    return render(request, "products/product_list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "brands": brands,
        "wishlist_ids": wishlist_ids,
        "price_stats": price_stats,
        "active_filters": active_filters,
        "sort": sort,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category", "brand"), slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:6]

    if request.user.is_authenticated:
        from .models import RecentlyViewed
        RecentlyViewed.objects.update_or_create(user=request.user, product=product)

    return render(request, "products/product_detail.html", {"product": product, "related": related})


@login_required
def seller_product_list(request):
    products = Product.objects.filter(seller=request.user)
    return render(request, "products/seller_product_list.html", {"products": products})
