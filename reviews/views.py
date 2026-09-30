from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from products.models import Product
from orders.models import OrderItem
from .forms import ReviewForm
from .models import Review


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review, _ = Review.objects.update_or_create(
                product=product, user=request.user,
                defaults={**form.cleaned_data,
                          "is_verified_purchase": OrderItem.objects.filter(order__user=request.user, product=product).exists()},
            )
            messages.success(request, "Thanks for your review!")
            return redirect("products:product_detail", product.slug)
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect("products:product_detail", product.slug)


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product = review.product
    review.delete()
    messages.info(request, "Review deleted.")
    return redirect("products:product_detail", product.slug)
