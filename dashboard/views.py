from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import render, redirect

from .forms import SellerRegistrationForm
from .models import SellerProfile
from products.models import Product
from orders.models import OrderItem


@login_required
def seller_register(request):
    if request.user.is_seller:
        return redirect("dashboard:seller_dashboard")
    if request.method == "POST":
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            request.user.is_seller = True
            request.user.save(update_fields=["is_seller"])
            messages.success(request, "Seller account created! Start adding products.")
            return redirect("dashboard:seller_dashboard")
    else:
        form = SellerRegistrationForm()
    return render(request, "dashboard/seller_register.html", {"form": form})


@login_required
def seller_dashboard(request):
    products = Product.objects.filter(seller=request.user)
    sold_items = OrderItem.objects.filter(product__seller=request.user)
    total_sales = sold_items.aggregate(total=Sum("price"))["total"] or 0
    total_orders = sold_items.values("order").distinct().count()
    low_stock = products.filter(stock__lte=5, stock__gt=0)
    out_of_stock = products.filter(stock=0)

    return render(request, "dashboard/seller_dashboard.html", {
        "products": products, "total_sales": total_sales, "total_orders": total_orders,
        "low_stock": low_stock, "out_of_stock": out_of_stock,
    })
