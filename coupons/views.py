from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from cart.models import Cart
from .models import Coupon


@login_required
def apply_coupon(request):
    if request.method == "POST":
        code = request.POST.get("code", "").strip().upper()
        cart, _ = Cart.objects.get_or_create(user=request.user)
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid coupon code.")
            return redirect("cart:cart_detail")

        if coupon.is_valid(cart.subtotal):
            request.session["coupon_code"] = coupon.code
            messages.success(request, f"Coupon {coupon.code} applied! You saved ₹{coupon.calculate_discount(cart.subtotal)}.")
        else:
            messages.error(request, "This coupon is not valid for your order.")
    return redirect("cart:cart_detail")


@login_required
def remove_coupon(request):
    request.session.pop("coupon_code", None)
    messages.info(request, "Coupon removed.")
    return redirect("cart:cart_detail")
